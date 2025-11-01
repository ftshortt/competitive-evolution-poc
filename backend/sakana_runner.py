"""Sakana Agent Runner

Manages SakanaAgent lifecycle, concurrency, evolution, and logging.
"""

import json
import logging
import random
import string
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from sakana_agent import SakanaAgent


logger = logging.getLogger(__name__)


def _gen_id(prefix: str = "ag") -> str:
    return f"{prefix}-" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))


class SakanaRunner:
    """Coordinator for running multiple Sakana agents concurrently."""

    def __init__(
        self,
        work_dir: str = "/workspace/sakana",
        max_concurrent_agents: int = 4,
        use_docker: bool = True,
        gpu_enabled: bool = False,
    ) -> None:
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)

        self.max_concurrent = max_concurrent_agents
        self.use_docker = use_docker
        self.gpu_enabled = gpu_enabled

        self._agents: Dict[str, SakanaAgent] = {}
        self._queue: deque[str] = deque()
        self._lock = threading.Lock()
        self._workers: List[threading.Thread] = []
        self._stop_event = threading.Event()

        # Resource tracking (simple)
        self._gpu_pool = list(range(0, 8)) if gpu_enabled else []

        # Start worker threads
        for i in range(self.max_concurrent):
            t = threading.Thread(target=self._worker_loop, name=f"sakana-worker-{i}", daemon=True)
            t.start()
            self._workers.append(t)

    # ---------- Public API ----------

    def create_agent(self, template: str, config: Dict[str, Any], parent_ids: List[str], generation: int) -> str:
        agent_id = _gen_id()
        cfg = dict(config)
        cfg.setdefault('generation', generation)
        cfg.setdefault('parent_ids', parent_ids)
        cfg.setdefault('work_dir', str(self.work_dir / agent_id))

        agent = SakanaAgent(agent_id=agent_id, template=template, config=cfg)
        with self._lock:
            self._agents[agent_id] = agent
            self._queue.append(agent_id)
        logger.info(f"Queued Sakana agent {agent_id} (gen {generation}) using template {template}")
        return agent_id

    def get_agent(self, agent_id: str) -> Optional[SakanaAgent]:
        with self._lock:
            return self._agents.get(agent_id)

    def get_all_agents(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [a.to_dict() for a in self._agents.values()]

    def terminate_agent(self, agent_id: str) -> None:
        agent = self.get_agent(agent_id)
        if agent:
            agent.terminate()

    def get_agent_logs(self, agent_id: str, tail: int = 100) -> List[str]:
        agent = self.get_agent(agent_id)
        if not agent:
            return []
        # Tail stdout from process if alive
        lines: List[str] = []
        if agent.process and agent.process.stdout:
            try:
                # Non-blocking read
                out = agent.process.stdout.read()
                if out:
                    lines = out.splitlines()[-tail:]
            except Exception:
                pass
        return lines

    def get_lineage_tree(self, agent_id: str) -> Dict[str, Any]:
        """Build a simple lineage tree."""
        with self._lock:
            agent = self._agents.get(agent_id)
            if not agent:
                return {}
            tree = {
                'agent_id': agent.agent_id,
                'generation': agent.generation,
                'parents': agent.parent_ids,
            }
            # Expand one level up for simplicity
            ancestors = []
            for pid in agent.parent_ids:
                p = self._agents.get(pid)
                if p:
                    ancestors.append({'agent_id': p.agent_id, 'generation': p.generation, 'parents': p.parent_ids})
            tree['ancestors'] = ancestors
            return tree

    def get_statistics(self) -> Dict[str, Any]:
        with self._lock:
            agents = list(self._agents.values())
        total = len(agents)
        running = sum(1 for a in agents if a.check_status() == 'running')
        completed = sum(1 for a in agents if a.status == 'completed')
        failed = sum(1 for a in agents if a.status == 'failed')
        fitness_values = [a.fitness_score for a in agents if a.fitness_score is not None]
        avg_fit = sum(fitness_values) / len(fitness_values) if fitness_values else 0.0
        best_fit = max(fitness_values) if fitness_values else 0.0
        generations = max([a.generation for a in agents], default=0)
        return {
            'total_agents': total,
            'running_agents': running,
            'completed_agents': completed,
            'failed_agents': failed,
            'average_fitness': avg_fit,
            'best_fitness': best_fit,
            'generations': generations,
        }

    def evolve(self, selection_size: int = 2, offspring_count: int = 4, mutation_rate: float = 0.1) -> List[str]:
        """Select top agents and spawn offspring with mutated configs."""
        with self._lock:
            completed = [a for a in self._agents.values() if a.status == 'completed' and a.fitness_score is not None]
        # Sort by fitness descending
        completed.sort(key=lambda a: a.fitness_score or 0.0, reverse=True)
        parents = completed[:selection_size]
        new_ids: List[str] = []
        if not parents:
            return new_ids

        for i in range(offspring_count):
            p = parents[i % len(parents)]
            cfg = dict(p.config)
            # Simple mutation: tweak numeric params slightly
            exp_params = cfg.get('experiment_params', {})
            for k, v in list(exp_params.items()):
                if isinstance(v, (int, float)) and random.random() < mutation_rate:
                    scale = 1 + random.uniform(-0.2, 0.2)
                    exp_params[k] = type(v)(max(0, v * scale))
            cfg['experiment_params'] = exp_params
            child_id = self.create_agent(template=p.template, config=cfg, parent_ids=[p.agent_id], generation=p.generation + 1)
            new_ids.append(child_id)
        return new_ids

    # ---------- Internal ----------

    def _worker_loop(self) -> None:
        while not self._stop_event.is_set():
            agent_id: Optional[str] = None
            with self._lock:
                if self._queue:
                    agent_id = self._queue.popleft()
            if not agent_id:
                time.sleep(0.2)
                continue
            agent = self.get_agent(agent_id)
            if not agent:
                continue

            gpu_id = None
            if self.gpu_enabled and self._gpu_pool:
                gpu_id = self._gpu_pool.pop(0)
            try:
                agent.run_experiment(use_docker=self.use_docker, gpu_id=gpu_id)
                # Poll until complete
                while agent.check_status() == 'running' and not self._stop_event.is_set():
                    time.sleep(2)
                # Return GPU to pool
            finally:
                if gpu_id is not None:
                    self._gpu_pool.append(gpu_id)

    def shutdown(self) -> None:
        self._stop_event.set()
        for t in self._workers:
            t.join(timeout=2)
        with self._lock:
            for a in self._agents.values():
                if a.status == 'running':
                    a.terminate()
