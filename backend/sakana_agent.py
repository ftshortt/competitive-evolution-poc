"""Sakana AI Agent Integration

This module provides a sample agent class for running Sakana AI-Scientist experiments
within the competitive evolution framework.
"""

import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


class SakanaAgent:
    """Agent wrapper for Sakana AI-Scientist experiments.
    
    This agent runs Sakana AI-Scientist templates as evolutionary experiments,
    capturing outputs, reviews, and PDFs for fitness evaluation.
    """
    
    def __init__(self, agent_id: str, template: str, config: Dict[str, Any]):
        """
        Initialize a Sakana agent.
        
        Args:
            agent_id: Unique identifier for this agent
            template: Sakana template name (e.g., 'nanoGPT', 'grokking')
            config: Configuration dictionary with experiment parameters
        """
        self.agent_id = agent_id
        self.template = template
        self.config = config
        self.generation = config.get('generation', 0)
        self.parent_ids = config.get('parent_ids', [])
        
        # Execution state
        self.status = 'initialized'
        self.process = None
        self.start_time = None
        self.end_time = None
        
        # Results
        self.experiment_output = None
        self.review_output = None
        self.fitness_score = None
        self.artifacts = {
            'logs': [],
            'plots': [],
            'pdfs': [],
            'checkpoints': []
        }
        
        # Paths
        self.work_dir = Path(config.get('work_dir', f'/workspace/agents/{agent_id}'))
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
    def run_experiment(self, use_docker: bool = True, gpu_id: Optional[int] = None) -> bool:
        """
        Launch the Sakana AI-Scientist experiment.
        
        Args:
            use_docker: If True, run in isolated Docker container
            gpu_id: GPU device ID for GPU passthrough (if available)
            
        Returns:
            bool: True if experiment launched successfully
        """
        self.status = 'running'
        self.start_time = datetime.now()
        
        try:
            if use_docker:
                return self._run_docker_experiment(gpu_id)
            else:
                return self._run_subprocess_experiment()
        except Exception as e:
            self.status = 'failed'
            self.experiment_output = {'error': str(e)}
            return False
    
    def _run_docker_experiment(self, gpu_id: Optional[int] = None) -> bool:
        """Run experiment in Docker container with isolation."""
        cmd = [
            'docker', 'run',
            '--rm',
            '-v', f'{self.work_dir}:/workspace',
            '--network', 'none',  # Network isolation for security
            '--memory', self.config.get('memory_limit', '16g'),
            '--cpus', str(self.config.get('cpu_limit', 4))
        ]
        
        # GPU passthrough if requested
        if gpu_id is not None:
            cmd.extend(['--gpus', f'device={gpu_id}'])
        
        # Add environment variables
        for key, value in self.config.get('env_vars', {}).items():
            cmd.extend(['-e', f'{key}={value}'])
        
        # Sakana AI-Scientist image and command
        cmd.extend([
            'sakana-ai-scientist:latest',
            'python', '-m', 'ai_scientist.experiment',
            '--template', self.template,
            '--output-dir', '/workspace/output',
            '--config', json.dumps(self.config.get('experiment_params', {}))
        ])
        
        # Launch subprocess
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        return True
    
    def _run_subprocess_experiment(self) -> bool:
        """Run experiment as subprocess (less isolated)."""
        cmd = [
            'python', '-m', 'ai_scientist.experiment',
            '--template', self.template,
            '--output-dir', str(self.work_dir / 'output'),
            '--config', json.dumps(self.config.get('experiment_params', {}))
        ]
        
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=self.config.get('ai_scientist_path', '/opt/ai-scientist')
        )
        
        return True
    
    def check_status(self) -> str:
        """Check current execution status."""
        if self.process is None:
            return self.status
        
        poll_result = self.process.poll()
        if poll_result is None:
            return 'running'
        elif poll_result == 0:
            self.status = 'completed'
            self.end_time = datetime.now()
            self._collect_results()
        else:
            self.status = 'failed'
            self.end_time = datetime.now()
        
        return self.status
    
    def _collect_results(self):
        """Collect experiment outputs and artifacts."""
        output_dir = self.work_dir / 'output'
        
        # Load experiment results
        results_file = output_dir / 'results.json'
        if results_file.exists():
            with open(results_file, 'r') as f:
                self.experiment_output = json.load(f)
        
        # Load review results
        review_file = output_dir / 'review.json'
        if review_file.exists():
            with open(review_file, 'r') as f:
                self.review_output = json.load(f)
        
        # Collect artifacts
        self.artifacts['logs'] = list(output_dir.glob('*.log'))
        self.artifacts['plots'] = list(output_dir.glob('**/*.png')) + list(output_dir.glob('**/*.pdf'))
        self.artifacts['pdfs'] = list(output_dir.glob('**/*.pdf'))
        self.artifacts['checkpoints'] = list(output_dir.glob('checkpoints/*'))
        
        # Calculate fitness from review scores
        if self.review_output:
            self.fitness_score = self._calculate_fitness()
    
    def _calculate_fitness(self) -> float:
        """Calculate fitness score from Sakana review output.
        
        Combines novelty, soundness, and impact scores from AI-Scientist review.
        """
        if not self.review_output:
            return 0.0
        
        # Extract review scores (Sakana AI-Scientist provides these)
        novelty = self.review_output.get('novelty', 0.0)
        soundness = self.review_output.get('soundness', 0.0)
        impact = self.review_output.get('impact', 0.0)
        
        # Also consider experiment performance metrics
        performance = 0.0
        if self.experiment_output:
            metrics = self.experiment_output.get('metrics', {})
            # Example: use validation accuracy or loss improvement
            performance = metrics.get('val_accuracy', 0.0)
        
        # Weighted combination
        fitness = (
            0.3 * novelty +
            0.3 * soundness +
            0.2 * impact +
            0.2 * performance
        )
        
        return fitness
    
    def terminate(self):
        """Forcefully terminate the experiment."""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            time.sleep(2)
            if self.process.poll() is None:
                self.process.kill()
        
        self.status = 'terminated'
        self.end_time = datetime.now()
    
    def get_lineage(self) -> List[str]:
        """Get agent lineage (parent IDs)."""
        return self.parent_ids
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize agent state to dictionary."""
        return {
            'agent_id': self.agent_id,
            'template': self.template,
            'generation': self.generation,
            'parent_ids': self.parent_ids,
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'fitness_score': self.fitness_score,
            'experiment_output': self.experiment_output,
            'review_output': self.review_output,
            'artifacts': {
                'logs': [str(p) for p in self.artifacts['logs']],
                'plots': [str(p) for p in self.artifacts['plots']],
                'pdfs': [str(p) for p in self.artifacts['pdfs']],
                'checkpoints': [str(p) for p in self.artifacts['checkpoints']]
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SakanaAgent':
        """Deserialize agent from dictionary."""
        agent = cls(
            agent_id=data['agent_id'],
            template=data['template'],
            config={
                'generation': data['generation'],
                'parent_ids': data['parent_ids']
            }
        )
        agent.status = data['status']
        agent.fitness_score = data['fitness_score']
        agent.experiment_output = data['experiment_output']
        agent.review_output = data['review_output']
        return agent
