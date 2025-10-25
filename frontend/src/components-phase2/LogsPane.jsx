import React, { useState, useEffect, useRef } from 'react';
import './LogsPane.css';

const LogsPane = () => {
  const [logs, setLogs] = useState([]);
  const [selectedPool, setSelectedPool] = useState('All');
  const [autoScroll, setAutoScroll] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);
  const logsEndRef = useRef(null);

  useEffect(() => {
    // WebSocket setup
    const connectWebSocket = () => {
      const wsUrl = `ws://${window.location.hostname}:8000/ws/logs`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setWsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const logData = JSON.parse(event.data);
          setLogs((prevLogs) => [...prevLogs, logData]);
        } catch (error) {
          console.error('Error parsing log message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setWsConnected(false);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setWsConnected(false);
        // Attempt to reconnect after 3 seconds
        setTimeout(() => {
          if (wsRef.current === ws) {
            connectWebSocket();
          }
        }, 3000);
      };

      wsRef.current = ws;
    };

    connectWebSocket();

    // Cleanup on unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    // Auto-scroll to bottom when new logs arrive
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  const getLogLevelClass = (level) => {
    switch (level?.toUpperCase()) {
      case 'ERROR':
        return 'log-error';
      case 'WARNING':
      case 'WARN':
        return 'log-warning';
      case 'INFO':
        return 'log-info';
      case 'DEBUG':
        return 'log-debug';
      default:
        return 'log-default';
    }
  };

  const filteredLogs = logs.filter((log) => {
    if (selectedPool === 'All') return true;
    return log.pool === selectedPool;
  });

  const handleClearLogs = () => {
    setLogs([]);
  };

  const handleExportLogs = () => {
    const logText = filteredLogs
      .map((log) => {
        const timestamp = new Date(log.timestamp).toISOString();
        return `[${timestamp}] [${log.level}] [${log.pool}] ${log.message}`;
      })
      .join('\n');

    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `logs_${selectedPool}_${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="logs-pane">
      <div className="logs-header">
        <h2>Real-time Logs</h2>
        <div className="connection-status">
          <span className={`status-indicator ${wsConnected ? 'connected' : 'disconnected'}`}></span>
          <span>{wsConnected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </div>

      <div className="logs-controls">
        <div className="filter-group">
          <label htmlFor="pool-filter">Filter Pool:</label>
          <select
            id="pool-filter"
            value={selectedPool}
            onChange={(e) => setSelectedPool(e.target.value)}
          >
            <option value="All">All</option>
            <option value="R1">R1</option>
            <option value="Qwen">Qwen</option>
          </select>
        </div>

        <div className="checkbox-group">
          <label>
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
            />
            Auto-scroll
          </label>
        </div>

        <div className="button-group">
          <button onClick={handleClearLogs} className="btn-clear">
            Clear Logs
          </button>
          <button onClick={handleExportLogs} className="btn-export" disabled={filteredLogs.length === 0}>
            Export Logs
          </button>
        </div>
      </div>

      <div className="logs-display">
        {filteredLogs.length === 0 ? (
          <div className="no-logs">No logs to display</div>
        ) : (
          filteredLogs.map((log, index) => (
            <div key={index} className={`log-entry ${getLogLevelClass(log.level)}`}>
              <span className="log-timestamp">
                {new Date(log.timestamp).toLocaleTimeString()}
              </span>
              <span className="log-level">[{log.level}]</span>
              <span className="log-pool">[{log.pool}]</span>
              <span className="log-message">{log.message}</span>
            </div>
          ))
        )}
        <div ref={logsEndRef} />
      </div>
    </div>
  );
};

export default LogsPane;
