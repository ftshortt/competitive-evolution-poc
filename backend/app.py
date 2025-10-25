from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import signal
from threading import Lock

app = Flask(__name__)
CORS(app)

# Global state for experiment management
experiment_process = None
experiment_lock = Lock()
experiment_stats = {
    'generation': 0,
    'fitness': 0.0,
    'pool_count': 0,
    'running': False
}

@app.route('/api/chat', methods=['POST'])
def chat():
    """Echo endpoint for chat messages"""
    data = request.get_json()
    message = data.get('message', '')
    return jsonify({
        'response': f"Echo: {message}",
        'status': 'success'
    })

@app.route('/api/experiment/start', methods=['POST'])
def start_experiment():
    """Start the competitive evolution experiment"""
    global experiment_process, experiment_stats
    
    with experiment_lock:
        if experiment_process and experiment_process.poll() is None:
            return jsonify({
                'status': 'error',
                'message': 'Experiment already running'
            }), 400
        
        try:
            # Spawn subprocess for competitive_evolution.py
            script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'competitive_evolution.py')
            experiment_process = subprocess.Popen(
                ['python', script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            experiment_stats['running'] = True
            
            return jsonify({
                'status': 'success',
                'message': 'Experiment started',
                'pid': experiment_process.pid
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

@app.route('/api/experiment/stop', methods=['POST'])
def stop_experiment():
    """Stop the running experiment"""
    global experiment_process, experiment_stats
    
    with experiment_lock:
        if not experiment_process or experiment_process.poll() is not None:
            return jsonify({
                'status': 'error',
                'message': 'No experiment running'
            }), 400
        
        try:
            # Terminate the process
            os.kill(experiment_process.pid, signal.SIGTERM)
            experiment_process.wait(timeout=5)
            experiment_stats['running'] = False
            
            return jsonify({
                'status': 'success',
                'message': 'Experiment stopped'
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current experiment status"""
    global experiment_stats
    
    # Check if process is still running
    if experiment_process:
        experiment_stats['running'] = experiment_process.poll() is None
    
    return jsonify({
        'generation': experiment_stats['generation'],
        'fitness': experiment_stats['fitness'],
        'pool_count': experiment_stats['pool_count'],
        'running': experiment_stats['running']
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
