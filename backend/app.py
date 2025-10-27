from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import signal
from threading import Lock

# Phase 2 imports
try:
    from backend.phase2.code_execution import code_execution_bp
    from backend.phase2.tagging_service import tagging_bp
    from backend.phase2.logs_streamer import logs_bp
    PHASE_2_AVAILABLE = True
except ImportError:
    PHASE_2_AVAILABLE = False

# Neo4j and models
from src.utils import Neo4jLineageTracker, Task, Solution, DEFAULT_DOMAIN

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

# Initialize tracker (read from env)
NEO4J_URI = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', 'evolution2025')
tracker = Neo4jLineageTracker(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

# Phase 1 routes (existing)
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

# New: Domain-aware APIs
@app.route('/api/entities/task', methods=['POST'])
def api_create_task():
    data = request.get_json(force=True)
    task = Task(
        id=data['id'],
        task_type=data.get('task_type', data.get('type', 'generic')),
        description=data.get('description', ''),
        test_cases=data.get('test_cases', []),
        difficulty=data.get('difficulty'),
        domain=(data.get('domain') or DEFAULT_DOMAIN)
    )
    node = tracker.create_task(task)
    return jsonify({'status': 'success', 'task': node})

@app.route('/api/entities/solution', methods=['POST'])
def api_create_solution():
    data = request.get_json(force=True)
    sol = Solution(
        id=data['id'],
        code=data.get('code', ''),
        reasoning_trace=data.get('reasoning_trace', ''),
        fitness=float(data.get('fitness', 0.0)),
        pool=data.get('pool', 'default'),
        pool_trait=data.get('pool_trait', ''),
        generation=int(data.get('generation', 0)),
        task_type=data.get('task_type', data.get('type', 'generic')),
        reasoning_steps=int(data.get('reasoning_steps', 0)),
        token_cost=int(data.get('token_cost', 0)),
        parent_ids=data.get('parent_ids', []),
        task_id=data.get('task_id'),
        execution_time=data.get('execution_time'),
        memory_usage=data.get('memory_usage'),
        domain=(data.get('domain') or DEFAULT_DOMAIN)
    )
    node = tracker.create_solution(sol)
    # Optionally link to parents
    for pid in sol.parent_ids:
        tracker.link_parent(sol.id, pid)
    # Optionally link to task
    if sol.task_id:
        tracker.link_solution_to_task(sol.id, sol.task_id)
    return jsonify({'status': 'success', 'solution': node})

@app.route('/api/entities/link', methods=['POST'])
def api_link_entities():
    data = request.get_json(force=True)
    left_label = data.get('left_label', 'Solution')
    left_id = data['left_id']
    rel = data.get('rel', 'RELATED_TO')
    right_label = data.get('right_label', 'Solution')
    right_id = data['right_id']
    attrs = data.get('attrs', {})
    tracker.link_cross_domain(left_label, left_id, rel, right_label, right_id, attrs)
    return jsonify({'status': 'success'})

@app.route('/api/entities/query/best', methods=['GET'])
def api_query_best():
    task_type = request.args.get('task_type')
    domain = request.args.get('domain')
    limit = int(request.args.get('limit', 10))
    rows = tracker.get_best_solutions(task_type=task_type, domain=domain, limit=limit)
    return jsonify({'status': 'success', 'items': rows})

@app.route('/api/entities/query/lineage/<solution_id>', methods=['GET'])
def api_query_lineage(solution_id: str):
    depth = int(request.args.get('depth', 5))
    rows = tracker.get_lineage(solution_id, max_depth=depth)
    return jsonify({'status': 'success', 'items': rows})

@app.route('/api/entities/query/pool_stats', methods=['GET'])
def api_query_pool_stats():
    pool = request.args['pool']
    domain = request.args.get('domain')
    stats = tracker.get_pool_statistics(pool=pool, domain=domain)
    return jsonify({'status': 'success', 'stats': stats})

@app.route('/api/entities/migrate/default_domain', methods=['POST'])
def api_migrate_default_domain():
    default_domain = (request.get_json(force=True) or {}).get('default_domain', DEFAULT_DOMAIN)
    s_count, t_count = tracker.migrate_assign_default_domain(default_domain)
    return jsonify({'status': 'success', 'solutions_updated': s_count, 'tasks_updated': t_count})

# Phase 2 blueprint registration with feature flag
if PHASE_2_AVAILABLE and os.environ.get('PHASE_2_ENABLED', 'false').lower() == 'true':
    app.register_blueprint(code_execution_bp, url_prefix='/api/phase2')
    app.register_blueprint(tagging_bp, url_prefix='/api/phase2')
    app.register_blueprint(logs_bp, url_prefix='/api/phase2')
    print("Phase 2 blueprints registered")
else:
    print("Phase 2 disabled or not available")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
