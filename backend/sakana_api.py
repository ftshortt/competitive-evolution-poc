"""Sakana AI API Endpoints

Extends the backend REST API to support launching Sakana experiments,
fetching results, logs, and managing Sakana agents.
"""

from flask import Blueprint, request, jsonify, send_file
from pathlib import Path
import json
import logging
from typing import Dict, Any, List

from sakana_agent import SakanaAgent
from sakana_runner import SakanaRunner


logger = logging.getLogger(__name__)

# Create blueprint for Sakana API routes
sakana_bp = Blueprint('sakana', __name__, url_prefix='/api/sakana')

# Global runner instance (initialized on app startup)
sakana_runner = None


def init_sakana_api(app_config: Dict[str, Any]):
    """Initialize the Sakana API with configuration.
    
    Args:
        app_config: Application configuration dictionary
    """
    global sakana_runner
    sakana_runner = SakanaRunner(
        work_dir=app_config.get('sakana_work_dir', '/workspace/sakana'),
        max_concurrent_agents=app_config.get('max_sakana_agents', 4),
        use_docker=app_config.get('sakana_use_docker', True),
        gpu_enabled=app_config.get('sakana_gpu_enabled', False)
    )
    logger.info("Sakana API initialized")


@sakana_bp.route('/templates', methods=['GET'])
def get_templates():
    """Get available Sakana AI-Scientist templates.
    
    Returns:
        JSON list of available templates with descriptions
    """
    templates = [
        {
            'name': 'nanoGPT',
            'description': 'Small-scale GPT language model experiments',
            'category': 'nlp',
            'estimated_runtime': '2-6 hours'
        },
        {
            'name': 'grokking',
            'description': 'Experiments on grokking phenomenon in neural networks',
            'category': 'theory',
            'estimated_runtime': '1-3 hours'
        },
        {
            'name': 'diffusion',
            'description': 'Diffusion model experiments',
            'category': 'generative',
            'estimated_runtime': '3-8 hours'
        },
        {
            'name': 'rl_basics',
            'description': 'Reinforcement learning fundamentals',
            'category': 'rl',
            'estimated_runtime': '1-4 hours'
        }
    ]
    return jsonify({'templates': templates})


@sakana_bp.route('/agents', methods=['GET'])
def get_agents():
    """Get all Sakana agents with their current status.
    
    Query params:
        status: Filter by status (running, completed, failed)
        generation: Filter by generation number
    
    Returns:
        JSON list of agents
    """
    status_filter = request.args.get('status')
    generation_filter = request.args.get('generation', type=int)
    
    agents = sakana_runner.get_all_agents()
    
    # Apply filters
    if status_filter:
        agents = [a for a in agents if a['status'] == status_filter]
    if generation_filter is not None:
        agents = [a for a in agents if a['generation'] == generation_filter]
    
    return jsonify({
        'agents': agents,
        'count': len(agents)
    })


@sakana_bp.route('/agents/<agent_id>', methods=['GET'])
def get_agent(agent_id: str):
    """Get detailed information about a specific agent.
    
    Args:
        agent_id: Unique agent identifier
    
    Returns:
        JSON agent details including outputs and artifacts
    """
    agent = sakana_runner.get_agent(agent_id)
    
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404
    
    return jsonify({'agent': agent.to_dict()})


@sakana_bp.route('/agents', methods=['POST'])
def create_agent():
    """Launch a new Sakana AI-Scientist experiment.
    
    Request body:
        template: Template name (required)
        config: Experiment configuration (optional)
        parent_ids: List of parent agent IDs for evolutionary lineage (optional)
    
    Returns:
        JSON with new agent ID and status
    """
    data = request.get_json()
    
    if not data or 'template' not in data:
        return jsonify({'error': 'Template is required'}), 400
    
    template = data['template']
    config = data.get('config', {})
    parent_ids = data.get('parent_ids', [])
    generation = data.get('generation', 0)
    
    try:
        # Create and launch agent
        agent_id = sakana_runner.create_agent(
            template=template,
            config=config,
            parent_ids=parent_ids,
            generation=generation
        )
        
        return jsonify({
            'agent_id': agent_id,
            'status': 'launched',
            'message': f'Sakana agent {agent_id} launched successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        return jsonify({'error': str(e)}), 500


@sakana_bp.route('/agents/<agent_id>/terminate', methods=['POST'])
def terminate_agent(agent_id: str):
    """Terminate a running agent.
    
    Args:
        agent_id: Unique agent identifier
    
    Returns:
        JSON status message
    """
    try:
        sakana_runner.terminate_agent(agent_id)
        return jsonify({
            'agent_id': agent_id,
            'status': 'terminated'
        })
    except Exception as e:
        logger.error(f"Failed to terminate agent {agent_id}: {e}")
        return jsonify({'error': str(e)}), 500


@sakana_bp.route('/agents/<agent_id>/logs', methods=['GET'])
def get_agent_logs(agent_id: str):
    """Get logs for a specific agent.
    
    Query params:
        tail: Number of lines to return from end (default: 100)
    
    Args:
        agent_id: Unique agent identifier
    
    Returns:
        JSON with log content
    """
    tail = request.args.get('tail', 100, type=int)
    
    agent = sakana_runner.get_agent(agent_id)
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404
    
    try:
        logs = sakana_runner.get_agent_logs(agent_id, tail=tail)
        return jsonify({
            'agent_id': agent_id,
            'logs': logs,
            'lines': len(logs)
        })
    except Exception as e:
        logger.error(f"Failed to get logs for agent {agent_id}: {e}")
        return jsonify({'error': str(e)}), 500


@sakana_bp.route('/agents/<agent_id>/results', methods=['GET'])
def get_agent_results(agent_id: str):
    """Get experiment results for an agent.
    
    Args:
        agent_id: Unique agent identifier
    
    Returns:
        JSON with experiment output and review
    """
    agent = sakana_runner.get_agent(agent_id)
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404
    
    return jsonify({
        'agent_id': agent_id,
        'status': agent.status,
        'experiment_output': agent.experiment_output,
        'review_output': agent.review_output,
        'fitness_score': agent.fitness_score
    })


@sakana_bp.route('/agents/<agent_id>/artifacts', methods=['GET'])
def get_agent_artifacts(agent_id: str):
    """Get list of artifacts (plots, PDFs, checkpoints) for an agent.
    
    Args:
        agent_id: Unique agent identifier
    
    Returns:
        JSON with artifact paths
    """
    agent = sakana_runner.get_agent(agent_id)
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404
    
    return jsonify({
        'agent_id': agent_id,
        'artifacts': agent.artifacts
    })


@sakana_bp.route('/agents/<agent_id>/artifacts/<path:artifact_path>', methods=['GET'])
def download_artifact(agent_id: str, artifact_path: str):
    """Download a specific artifact file.
    
    Args:
        agent_id: Unique agent identifier
        artifact_path: Relative path to artifact
    
    Returns:
        File download
    """
    agent = sakana_runner.get_agent(agent_id)
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404
    
    # Security check: ensure path is within agent's work directory
    work_dir = Path(agent.work_dir)
    artifact_full_path = (work_dir / artifact_path).resolve()
    
    if not artifact_full_path.is_relative_to(work_dir):
        return jsonify({'error': 'Invalid artifact path'}), 403
    
    if not artifact_full_path.exists():
        return jsonify({'error': 'Artifact not found'}), 404
    
    return send_file(artifact_full_path)


@sakana_bp.route('/agents/<agent_id>/lineage', methods=['GET'])
def get_agent_lineage(agent_id: str):
    """Get evolutionary lineage for an agent.
    
    Args:
        agent_id: Unique agent identifier
    
    Returns:
        JSON with parent and ancestor information
    """
    agent = sakana_runner.get_agent(agent_id)
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404
    
    lineage = sakana_runner.get_lineage_tree(agent_id)
    
    return jsonify({
        'agent_id': agent_id,
        'generation': agent.generation,
        'lineage': lineage
    })


@sakana_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get overall statistics for Sakana experiments.
    
    Returns:
        JSON with aggregate stats
    """
    stats = sakana_runner.get_statistics()
    
    return jsonify({
        'total_agents': stats['total_agents'],
        'running_agents': stats['running_agents'],
        'completed_agents': stats['completed_agents'],
        'failed_agents': stats['failed_agents'],
        'average_fitness': stats['average_fitness'],
        'best_fitness': stats['best_fitness'],
        'generations': stats['generations']
    })


@sakana_bp.route('/evolve', methods=['POST'])
def evolve_population():
    """Trigger evolutionary step: select top agents and spawn next generation.
    
    Request body:
        selection_size: Number of top agents to select as parents (default: 2)
        offspring_count: Number of offspring to generate (default: 4)
        mutation_rate: Rate of configuration mutation (default: 0.1)
    
    Returns:
        JSON with new agent IDs
    """
    data = request.get_json() or {}
    
    selection_size = data.get('selection_size', 2)
    offspring_count = data.get('offspring_count', 4)
    mutation_rate = data.get('mutation_rate', 0.1)
    
    try:
        new_agents = sakana_runner.evolve(
            selection_size=selection_size,
            offspring_count=offspring_count,
            mutation_rate=mutation_rate
        )
        
        return jsonify({
            'new_agents': new_agents,
            'count': len(new_agents),
            'message': f'Spawned {len(new_agents)} agents in next generation'
        })
        
    except Exception as e:
        logger.error(f"Evolution failed: {e}")
        return jsonify({'error': str(e)}), 500
