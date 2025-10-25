"""Real-time log streaming service with WebSocket support.

Provides Flask-SocketIO integration for streaming logs to connected clients
with support for pool filtering, log level parsing, and historical log buffering.
"""

import os
import time
import threading
from collections import deque
from pathlib import Path
from flask_socketio import SocketIO, emit, Namespace
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import re


class LogBuffer:
    """Thread-safe buffer for managing historical logs."""
    
    def __init__(self, maxlen=1000):
        self.buffer = deque(maxlen=maxlen)
        self.lock = threading.Lock()
    
    def add(self, log_entry):
        """Add a log entry to the buffer."""
        with self.lock:
            self.buffer.append(log_entry)
    
    def get_all(self):
        """Get all buffered log entries."""
        with self.lock:
            return list(self.buffer)
    
    def clear(self):
        """Clear the buffer."""
        with self.lock:
            self.buffer.clear()


class LogParser:
    """Parse log entries and extract metadata."""
    
    LOG_LEVEL_PATTERN = re.compile(
        r'\[(INFO|ERROR|WARNING|DEBUG|CRITICAL)\]',
        re.IGNORECASE
    )
    
    @staticmethod
    def parse_log_line(line):
        """Parse a log line and extract level and content.
        
        Args:
            line: Raw log line string
            
        Returns:
            dict: Parsed log entry with 'level', 'message', 'timestamp', 'raw'
        """
        match = LogParser.LOG_LEVEL_PATTERN.search(line)
        level = match.group(1).upper() if match else 'INFO'
        
        return {
            'level': level,
            'message': line.strip(),
            'timestamp': time.time(),
            'raw': line
        }
    
    @staticmethod
    def filter_by_level(log_entry, levels):
        """Check if log entry matches specified levels.
        
        Args:
            log_entry: Parsed log entry dict
            levels: List of log levels to include (e.g., ['INFO', 'ERROR'])
            
        Returns:
            bool: True if log entry matches one of the specified levels
        """
        if not levels:
            return True
        return log_entry['level'] in [l.upper() for l in levels]


class LogFileHandler(FileSystemEventHandler):
    """Handle file system events for log files."""
    
    def __init__(self, callback):
        self.callback = callback
        super().__init__()
    
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory and event.src_path.endswith('.log'):
            self.callback(event.src_path)
    
    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory and event.src_path.endswith('.log'):
            self.callback(event.src_path)


class LogsNamespace(Namespace):
    """SocketIO namespace for log streaming."""
    
    def __init__(self, namespace, log_buffer, logs_dir):
        super().__init__(namespace)
        self.log_buffer = log_buffer
        self.logs_dir = Path(logs_dir)
        self.active_files = {}
        self.client_filters = {}  # Store filter preferences per client
    
    def on_connect(self):
        """Handle client connection."""
        print(f'Client connected to /logs namespace: {threading.current_thread().name}')
        # Send historical logs to newly connected client
        historical_logs = self.log_buffer.get_all()
        emit('historical_logs', {'logs': historical_logs})
    
    def on_disconnect(self):
        """Handle client disconnection."""
        print(f'Client disconnected from /logs namespace')
        # Clean up client-specific filters
        client_id = threading.current_thread().name
        if client_id in self.client_filters:
            del self.client_filters[client_id]
    
    def on_subscribe(self, data):
        """Handle subscription to specific log sources.
        
        Args:
            data: dict with 'pool' (optional) and 'levels' (optional) filters
        """
        pool = data.get('pool', None)
        levels = data.get('levels', [])
        client_id = threading.current_thread().name
        
        self.client_filters[client_id] = {
            'pool': pool,
            'levels': levels
        }
        
        emit('subscribed', {
            'pool': pool,
            'levels': levels,
            'message': 'Successfully subscribed to log stream'
        })
    
    def on_unsubscribe(self, data):
        """Handle unsubscription from log sources."""
        client_id = threading.current_thread().name
        if client_id in self.client_filters:
            del self.client_filters[client_id]
        
        emit('unsubscribed', {'message': 'Unsubscribed from log stream'})
    
    def on_request_history(self, data):
        """Handle request for historical logs.
        
        Args:
            data: dict with optional 'pool' and 'levels' filters
        """
        pool = data.get('pool', None)
        levels = data.get('levels', [])
        
        historical_logs = self.log_buffer.get_all()
        filtered_logs = self._filter_logs(historical_logs, pool, levels)
        
        emit('historical_logs', {'logs': filtered_logs})
    
    def _filter_logs(self, logs, pool=None, levels=None):
        """Filter logs by pool and levels.
        
        Args:
            logs: List of log entries
            pool: Pool name to filter by (None for all)
            levels: List of log levels to include (empty for all)
            
        Returns:
            list: Filtered log entries
        """
        filtered = []
        for log in logs:
            # Filter by level
            if levels and not LogParser.filter_by_level(log, levels):
                continue
            
            # Filter by pool (check if pool name is in message)
            if pool and pool not in log.get('message', ''):
                continue
            
            filtered.append(log)
        
        return filtered
    
    def broadcast_log(self, log_entry):
        """Broadcast log entry to all connected clients with appropriate filters.
        
        Args:
            log_entry: Parsed log entry dict
        """
        # Add to buffer
        self.log_buffer.add(log_entry)
        
        # Broadcast to all clients (they will filter on their end)
        # For server-side filtering, we would iterate through client_filters
        self.emit('new_log', log_entry)


class LogStreamer:
    """Main log streaming service."""
    
    def __init__(self, socketio, logs_dir='logs', buffer_size=1000):
        """Initialize the log streamer.
        
        Args:
            socketio: Flask-SocketIO instance
            logs_dir: Directory to watch for log files
            buffer_size: Maximum number of log entries to buffer
        """
        self.socketio = socketio
        self.logs_dir = Path(logs_dir)
        self.log_buffer = LogBuffer(maxlen=buffer_size)
        self.observer = None
        self.file_positions = {}  # Track read positions for each file
        self.running = False
        
        # Create logs directory if it doesn't exist
        self.logs_dir.mkdir(exist_ok=True)
        
        # Register namespace
        self.namespace = LogsNamespace('/logs', self.log_buffer, logs_dir)
        self.socketio.on_namespace(self.namespace)
    
    def start(self):
        """Start watching log files."""
        if self.running:
            return
        
        self.running = True
        
        # Read existing log files
        self._read_existing_logs()
        
        # Start file watcher
        event_handler = LogFileHandler(self._on_log_file_changed)
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.logs_dir), recursive=False)
        self.observer.start()
        
        print(f'LogStreamer started, watching: {self.logs_dir}')
    
    def stop(self):
        """Stop watching log files."""
        if not self.running:
            return
        
        self.running = False
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        print('LogStreamer stopped')
    
    def _read_existing_logs(self):
        """Read existing log files and populate buffer."""
        for log_file in self.logs_dir.glob('*.log'):
            self._read_log_file(str(log_file), initial=True)
    
    def _read_log_file(self, filepath, initial=False):
        """Read a log file and broadcast new entries.
        
        Args:
            filepath: Path to log file
            initial: If True, read all lines; if False, read only new lines
        """
        try:
            with open(filepath, 'r') as f:
                # Seek to last known position
                if not initial and filepath in self.file_positions:
                    f.seek(self.file_positions[filepath])
                elif initial:
                    # For initial read, read last N lines only to avoid overwhelming
                    lines = f.readlines()
                    lines = lines[-100:]  # Only last 100 lines for initial load
                    for line in lines:
                        if line.strip():
                            log_entry = LogParser.parse_log_line(line)
                            self.log_buffer.add(log_entry)
                    self.file_positions[filepath] = f.tell()
                    return
                
                # Read new lines
                for line in f:
                    if line.strip():
                        log_entry = LogParser.parse_log_line(line)
                        self.namespace.broadcast_log(log_entry)
                
                # Update position
                self.file_positions[filepath] = f.tell()
        
        except Exception as e:
            print(f'Error reading log file {filepath}: {e}')
    
    def _on_log_file_changed(self, filepath):
        """Callback for when a log file changes.
        
        Args:
            filepath: Path to changed log file
        """
        self._read_log_file(filepath, initial=False)


def init_log_streamer(socketio, logs_dir='logs', buffer_size=1000):
    """Initialize and start the log streamer.
    
    Args:
        socketio: Flask-SocketIO instance
        logs_dir: Directory to watch for log files
        buffer_size: Maximum number of log entries to buffer
        
    Returns:
        LogStreamer: Initialized log streamer instance
    """
    streamer = LogStreamer(socketio, logs_dir, buffer_size)
    streamer.start()
    return streamer


if __name__ == '__main__':
    # Example usage
    from flask import Flask
    from flask_socketio import SocketIO
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key'
    socketio = SocketIO(app, cors_allowed_origins='*')
    
    # Initialize log streamer
    streamer = init_log_streamer(socketio, logs_dir='logs', buffer_size=1000)
    
    try:
        print('Starting SocketIO server on port 5000...')
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print('Shutting down...')
        streamer.stop()
