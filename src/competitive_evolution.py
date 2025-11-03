import os
import time
import random
from typing import Dict, Any, List, Tuple, Optional
from copy import deepcopy

from openai import OpenAI
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

from src.utils import Solution, Task, Neo4jLineageTracker
from src.production_fitness import ProductionFitnessEvaluator
# Import DeepSeek-OCR agent
from src.deepseek_ocr import DeepSeekOCRAgent

"""
Competitive Evolution Orchestrator

This module now supports in-run weight updates, parameter merging/mixing, and
mutation-based offspring generation for all registered agents, including
DeepSeek-OCR. The design mirrors the AZR project’s demonstrated live weight
update and hybridization pattern while staying backend-agnostic.

Core additions:
- AgentWeightMixin: a minimal interface for load/save/update of weights
- merge_weights and mutate_weights utilities for hybrid offspring
- Evolution loop hooks that: evaluate -> select -> reproduce(merge/mutate) -> update
- Lineage tracking with explicit parentage in Neo4j

Note: For non-local/hosted API models that do not expose raw weights, the
"weights" are treated as model-state config: system prompts, adapters,
hyperparameters, OCR post-processing params, etc. These are still heritable
and evolvable and map to concrete behavior change across generations.
"""

# Configuration
R1_ENDPOINT = os.getenv("R1_ENDPOINT", "http://localhost:8001/v1")
QWEN_ENDPOINT = os.getenv("QWEN_ENDPOINT", "http://localhost:8002/v1")
# DeepSeek-OCR endpoint configuration (uses REST/image pipeline)
DEEPSEEK_OCR_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
PROMETHEUS_GATEWAY = os.getenv("PROMETHEUS_GATEWAY", "localhost:9091")

# Prometheus metrics setup
registry = CollectorRegistry()
shinka_fitness = Gauge('shinka_fitness', 'Fitness score from Shinka evaluation', ['model', 'generation'], registry=registry)
dgm_performance_gain = Gauge('dgm_performance_gain', 'Performance gain metric', ['model', 'generation'], registry=registry)
generation_count = Gauge('generation_count', 'Current generation number', registry=registry)
gpu_memory_mb = Gauge('gpu_memory_mb', 'GPU memory usage in MB', ['gpu_id'], registry=registry)
gpu_utilization_percent = Gauge('gpu_utilization_percent', 'GPU utilization percentage', ['gpu_id'], registry=registry)
cpu_utilization_percent = Gauge('cpu_utilization_percent', 'CPU utilization percentage', registry=registry)
vllm_r1_health = Gauge('vllm_r1_health', 'Health status of R1 vLLM endpoint (1=healthy, 0=unhealthy)', registry=registry)
vllm_qwen_health = Gauge('vllm_qwen_health', 'Health status of Qwen vLLM endpoint (1=healthy, 0=unhealthy)', registry=registry)
# DeepSeek-OCR health metric
vllm_deepseek_ocr_health = Gauge('vllm_deepseek_ocr_health', 'Health status of DeepSeek-OCR endpoint (1=healthy, 0=unhealthy)', registry=registry)
inference_latency_ms = Gauge('inference_latency_ms', 'Inference latency in milliseconds', ['model', 'generation'], registry=registry)


# ---- Weight mixin and utilities ------------------------------------------------
class AgentWeightMixin:
    """Lightweight interface for agents that support weight/state updates.

    Agents should implement:
      - get_weights(): return Dict[str, Any]
      - set_weights(weights: Dict[str, Any]) -> None
      - update_weights(delta: Dict[str, Any]) -> None

    For API-only models, treat "weights" as a Serializable config/state.
    """
    def get_weights(self) -> Dict[str, Any]:
        raise NotImplementedError

    def set_weights(self, weights: Dict[str, Any]) -> None:
        raise NotImplementedError

    def update_weights(self, delta: Dict[str, Any]) -> None:
        merged = deepcopy(self.get_weights())
        for k, v in (delta or {}).items():
            merged[k] = v
        self.set_weights(merged)


def merge_weights(a: Dict[str, Any], b: Dict[str, Any], alpha: float = 0.5) -> Dict[str, Any]:
    """Merge/mix two weight dicts. Numeric fields are linearly mixed, others prefer A then B.
    Mirrors AZR-style hybridization while keeping safe fallbacks.
    """
    out: Dict[str, Any] = {}
    keys = set(a.keys()) | set(b.keys())
    for k in keys:
        va, vb = a.get(k), b.get(k)
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
            out[k] = alpha * va + (1 - alpha) * vb
        elif isinstance(va, dict) and isinstance(vb, dict):
            out[k] = merge_weights(va, vb, alpha)
        else:
            out[k] = va if va is not None else vb
    return out


def mutate_weights(w: Dict[str, Any], rate: float = 0.1, noise: float = 0.05) -> Dict[str, Any]:
    """Apply simple mutations to numeric fields, random flips to booleans, shuffle choices.
    """
    out = deepcopy(w)
    for k, v in out.items():
        if isinstance(v, (int, float)) and random.random() < rate:
            jitter = (random.random() * 2 - 1) * noise * (abs(v) + 1e-6)
            out[k] = v + jitter
        elif isinstance(v, bool) and random.random() < rate:
            out[k] = not v
        elif isinstance(v, dict):
            out[k] = mutate_weights(v, rate, noise)
        # Lists/strings left as-is unless future strategies are added
    return out


# ---- Example wrappers for existing agents -------------------------------------
class EvolvableDeepSeekOCR(DeepSeekOCRAgent, AgentWeightMixin):
    """Wrap DeepSeekOCRAgent with evolvable state.

    We treat OCR parameters (e.g., resize_scale, binarize_threshold, lang hints,
    postprocessors) as weights. If the base agent already exposes such fields,
    we bridge them here. Otherwise we store into an internal state dict and use
    them at call time.
    """
    def __init__(self, api_key: str, base_config: Optional[Dict[str, Any]] = None):
        super().__init__(api_key=api_key)
        self._weights: Dict[str, Any] = base_config or {
            'resize_scale': 1.0,
            'binarize_threshold': 0.5,
            'language_hint': 'en',
            'enable_layout': True,
            'postprocess': {
                'merge_lines': True,
                'spellcheck': False,
            },
        }

    def get_weights(self) -> Dict[str, Any]:
        return deepcopy(self._weights)

    def set_weights(self, weights: Dict[str, Any]) -> None:
        self._weights = deepcopy(weights)

    # Example of using weights during inference
    def ocr(self, image_bytes: bytes) -> Dict[str, Any]:
        cfg = self.get_weights()
        return super().ocr(
            image_bytes,
            resize_scale=cfg.get('resize_scale', 1.0),
            binarize_threshold=cfg.get('binarize_threshold', 0.5),
            language_hint=cfg.get('language_hint', 'en'),
            enable_layout=cfg.get('enable_layout', True),
            postprocess=cfg.get('postprocess', {}),
        )


# TODO: Wrap other agents (R1, Qwen) similarly when local weights/config are accessible.


# ---- Evolution loop ------------------------------------------------------------
class Offspring:
    def __init__(self, name: str, weights: Dict[str, Any], parents: Tuple[str, str], alpha: float, mutation_rate: float):
        self.name = name
        self.weights = weights
        self.parents = parents
        self.alpha = alpha
        self.mutation_rate = mutation_rate


def produce_offspring(parent_a: AgentWeightMixin, parent_b: AgentWeightMixin, name: str,
                      alpha: float = 0.5, mutation_rate: float = 0.1, noise: float = 0.05) -> Offspring:
    wa, wb = parent_a.get_weights(), parent_b.get_weights()
    mixed = merge_weights(wa, wb, alpha=alpha)
    mutated = mutate_weights(mixed, rate=mutation_rate, noise=noise)
    return Offspring(name=name, weights=mutated, parents=(type(parent_a).__name__, type(parent_b).__name__),
                     alpha=alpha, mutation_rate=mutation_rate)


def evaluate_agent_on_tasks(agent_name: str, agent_obj: Any, tasks: List[Task]) -> float:
    """Stub evaluation returning average fitness using ProductionFitnessEvaluator.
    Replace/extend with actual scoring for your domain.
    """
    evaluator = ProductionFitnessEvaluator()
    scores = []
    for t in tasks:
        try:
            start = time.time()
            # Example: route by capability
            if isinstance(agent_obj, EvolvableDeepSeekOCR) and hasattr(t, 'image_bytes'):
                _ = agent_obj.ocr(t.image_bytes)
            else:
                # For text/code agents you would call agent_obj.generate(...)
                pass
            latency_ms = (time.time() - start) * 1000
            inference_latency_ms.labels(model=agent_name, generation=str(t.generation)).set(latency_ms)
            score = evaluator.evaluate(t)  # Domain-specific
            scores.append(score)
        except Exception:
            scores.append(0.0)
    return sum(scores) / max(1, len(scores))


def log_lineage(lineage: Neo4jLineageTracker, child: Offspring, generation: int, fitness: float) -> None:
    lineage.add_offspring(
        name=child.name,
        parents=list(child.parents),
        weights_summary={k: v for k, v in child.weights.items() if isinstance(v, (int, float, bool))},
        generation=generation,
        fitness=fitness,
        metadata={'alpha': child.alpha, 'mutation_rate': child.mutation_rate},
    )


def main():
    """Main orchestration for competitive evolution with weight updates and offspring.

    Steps:
    1) Initialize agents and their evolvable wrappers
    2) Evaluate population on tasks
    3) Select top performers
    4) Reproduce: merge/mix + mutate to produce offspring
    5) Update agent weights with offspring
    6) Track lineage and metrics; repeat for N generations
    """
    print("Initializing Competitive Evolution System...")
    print("Agents: R1, Qwen2.5-Coder, DeepSeek-OCR (evolvable)")

    # Instantiate agents (only OCR wrapped for now)
    ocr_agent = EvolvableDeepSeekOCR(api_key=DEEPSEEK_OCR_API_KEY)

    # Prepare tasks (placeholder/example list)
    tasks: List[Task] = []  # Fill with domain tasks; ensure generation field exists if used

    lineage = Neo4jLineageTracker()

    population: List[Tuple[str, AgentWeightMixin]] = [
        ("deepseek_ocr", ocr_agent),
    ]

    generations = 3
    for gen in range(generations):
        generation_count.set(gen)
        push_to_gateway(PROMETHEUS_GATEWAY, job='evoagent', registry=registry)

        # Evaluate
        fitness_scores: List[Tuple[str, float]] = []
        for name, agent in population:
            fitness = evaluate_agent_on_tasks(name, agent, tasks)
            shinka_fitness.labels(model=name, generation=str(gen)).set(fitness)
            fitness_scores.append((name, fitness))

        # Select top 2 (or less if small pop)
        fitness_scores.sort(key=lambda x: x[1], reverse=True)
        parents: List[Tuple[str, AgentWeightMixin]] = []
        by_name: Dict[str, AgentWeightMixin] = {n: a for n, a in population}
        for i in range(min(2, len(fitness_scores))):
            pname = fitness_scores[i][0]
            parents.append((pname, by_name[pname]))

        # If we have at least two parents, create child
        new_population: List[Tuple[str, AgentWeightMixin]] = population[:]
        if len(parents) >= 2:
            (a_name, a_agent), (b_name, b_agent) = parents[0], parents[1]
            child = produce_offspring(a_agent, b_agent, name=f"child_{gen}_{a_name}_{b_name}", alpha=0.6, mutation_rate=0.12)

            # Apply offspring weights to a copy of one parent (or a new agent instance)
            child_agent = EvolvableDeepSeekOCR(api_key=DEEPSEEK_OCR_API_KEY)
            child_agent.set_weights(child.weights)
            new_population.append((child.name, child_agent))

            # Evaluate child immediately for logging
            child_fitness = evaluate_agent_on_tasks(child.name, child_agent, tasks)
            log_lineage(lineage, child, generation=gen, fitness=child_fitness)

        population = new_population

    print("Evolution complete.")


if __name__ == "__main__":
    main()
