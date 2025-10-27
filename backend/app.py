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

# Agent lifecycle
from backend.agent_lifecycle import LifecycleManager

# Optional: AS-FDVM integration placeholder (adapt to your project structure)
try:
    from src.as_fdvm import evaluate_agent  # expected signature: evaluate_agent(agent_dict) -> fitness float
    AS_FDVM_AVAILABLE = True
except Exception:
    AS_FDVM_AVAILABLE = False

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

# Instantiate Lifecycle Manager with existing Neo4j driver when available
neo4j_driver = getattr(tracker, 'driver', None)
lifecycle = LifecycleManager(neo4j_driver=neo4j_driver)

# Bootstrap a persistent parent agent if none exists
if not lifecycle.root_agents:
    root = lifecycle.create_root_agent(traits={'role': 'parent', 'domain': 'general'}, name='Parent Agent')

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

# Existing endpoints omitted for brevity in this view... kept below

# Agent Lifecycle API
@app.route('/api/agent/spawn', methods=['POST'])
def api_agent_spawn():
    data = request.get_json(force=True) or {}
    parent_id = data.get('parent_id') or (lifecycle.root_agents[0].id if lifecycle.root_agents else None)
    traits = data.get('traits') or {}
    name = data.get('name')
    if not parent_id:
        return jsonify({'status': 'error', 'message': 'No parent available to spawn from'}), 400
    try:
        child = lifecycle.spawn_child_agent(parent_id, traits_override=traits, name=name)
        # Evaluate fitness via AS-FDVM if available
        if AS_FDVM_AVAILABLE:
            try:
                fitness = evaluate_agent(child.to_dict())
                lifecycle.evaluate_fitness(child.id, {
                    'interaction_count': child.interaction_count,
                    'accuracy': fitness,
                    'domain_expertise': 0.5
                })
            except Exception:
                pass
        return jsonify({'status': 'success', 'agent': child.to_dict()})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/agent/retire', methods=['POST'])
def api_agent_retire():
    data = request.get_json(force=True) or {}
    agent_id = data.get('agent_id')
    if not agent_id:
        return jsonify({'status': 'error', 'message': 'agent_id is required'}), 400
    try:
        agent = lifecycle.retire_agent(agent_id)
        return jsonify({'status': 'success', 'agent': agent.to_dict()})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/agent/status', methods=['GET'])
def api_agent_status():
    live = [a.to_dict() for a in lifecycle.get_live_agents()]
    metrics = lifecycle.get_metrics()
    return jsonify({'status': 'success', 'live_agents': live, 'metrics': metrics})

@app.route('/api/agent/family/<agent_id>', methods=['GET'])
def api_agent_family(agent_id: str):
    tree = lifecycle.get_family_tree(agent_id)
    if not tree:
        return jsonify({'status': 'error', 'message': 'Agent not found'}), 404
    return jsonify({'status': 'success', 'tree': tree})

@app.route('/api/agent/topic', methods=['POST'])
def api_agent_topic():
    data = request.get_json(force=True) or {}
    agent_id = data.get('agent_id')
    topic = data.get('topic')
    category = data.get('category')
    if not agent_id or not topic:
        return jsonify({'status': 'error', 'message': 'agent_id and topic required'}), 400
    lifecycle.log_topic_drift(agent_id, topic, category)
    return jsonify({'status': 'success'})

# Auto retirement cron-like endpoint (can be called by FE or scheduler)
@app.route('/api/agent/auto_retire', methods=['POST'])
def api_agent_auto_retire():
    threshold = float((request.get_json() or {}).get('threshold', 0.2))
    retired = lifecycle.auto_retire_low_fitness_agents(threshold=threshold)
    return jsonify({'status': 'success', 'retired': retired})

# Existing entity endpoints remain intact below
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
