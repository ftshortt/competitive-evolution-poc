# EvoAgent

## Overview

EvoAgent is an evolutionary AI system that enables agents to adapt, compete, and improve through natural selection principles. Built on the AS-FDVM (Adaptive Search - Fractal Darwinian Virtual Machines) architecture, EvoAgent creates a competitive ecosystem where multiple AI agents evolve solutions through mutation, adaptation, and competitive evolution.

### Key Benefits

- Self-Improving Agents: Agents autonomously update their weights, merge strategies, and produce offspring with enhanced capabilities
- Competitive Evolution: Multiple specialized agents (DeepSeek-R1, Qwen2.5-Coder, DeepSeek-OCR) compete and evolve simultaneously
- Adaptive Intelligence: Dynamic categorization across exploration, exploitation, innovation, stabilization, and adaptation strategies
- Fractal Architecture: Hierarchical agent spawning with parent-child relationships and generational tracking
- Real-time Monitoring: Built-in metrics, graph visualization, and drift detection for evolutionary progress

## Evolutionary Weight Updates and Hybridization (NEW)

Patterned after the AZR project's live weight-update and hybridization demos, EvoAgent now supports:

- In-run weight updates: Agents can update weights/state without restarts via a standard interface
- Merge/mix/mutation: Parents can be merged (alpha-blend), mixed recursively, and mutated to spawn offspring
- Offspring lineage: Parentage and weight summaries are recorded to Neo4j for transparent evolution tracking
- API-only models support: For hosted models without raw weight access, "weights" are evolvable configuration/state (prompts, adapters, thresholds, OCR options) that drive measurable behavior changes

Code highlights:

- src/competitive_evolution.py
  - AgentWeightMixin with get_weights/set_weights/update_weights
  - merge_weights and mutate_weights utilities (AZR-style hybridization)
  - produce_offspring(...) pipeline and lineage logging
  - Generation loop to evaluate, select, reproduce, and update

- src/deepseek_ocr.py
  - DeepSeekOCRAgent now accepts evolvable config via ocr(image_bytes, ...)
  - Evolvable wrapper class in competitive_evolution.py (EvolvableDeepSeekOCR) treats OCR knobs as weights

## What's New

### Evolvable Agent Wrappers (NEW)

**DeepSeek-R1 Agent** (`src/deepseek_r1.py`)
- Evolvable wrapper for DeepSeek-R1 reasoning model
- Configurable parameters: temperature, max_tokens, reasoning_effort (low/medium/high)
- Full get/set/update_weights support for evolutionary optimization
- Stub API implementation ready for integration
- Mutation and crossover methods for offspring generation

**Qwen2.5-Coder Agent** (`src/qwen_coder.py`)
- Evolvable wrapper for Qwen2.5-Coder coding model
- Configurable parameters: temperature, max_tokens, top_p, top_k, repetition_penalty
- Code generation and analysis capabilities
- Full get/set/update_weights support
- Mutation and crossover methods for genetic algorithms
- Context-aware code generation

**Usage Example:**
```python
from src.deepseek_r1 import EvolvableDeepSeekR1
from src.qwen_coder import EvolvableQwenCoder

# Initialize agents
r1_agent = EvolvableDeepSeekR1(
    api_key="your-key",
    temperature=1.0,
    reasoning_effort="medium"
)

qwen_agent = EvolvableQwenCoder(
    api_key="your-key",
    temperature=0.7,
    top_p=0.95
)

# Get current configuration
weights = r1_agent.get_weights()

# Update configuration
r1_agent.update_weights({"temperature": 0.1})

# Create mutated offspring
offspring = r1_agent.mutate(mutation_rate=0.1)

# Generate code with Qwen
result = qwen_agent.generate_code(
    "Write a function to calculate Fibonacci numbers",
    system_prompt="You are an expert Python developer"
)
```

### DeepSeek-OCR Integration

- Third Competitive Agent: DeepSeek-OCR added for OCR and document understanding
- Module: src/deepseek_ocr.py – provides DeepSeekOCRAgent class with an API scaffold
- Agent Features:
  - Image/document OCR (pipeline scaffold), stats tracking
  - Evolvable configuration knobs: resize_scale, binarize_threshold, language_hint, layout, postprocess
- Competitive Evolution: Participates alongside R1 and Qwen in the evolution loop
- Configuration: Set DEEPSEEK_API_KEY for API access

## Roadmap / Future Enhancements

- Complete API integration for DeepSeek-R1, Qwen2.5-Coder, and DeepSeek-OCR (currently stub implementations)
- Add crossover operators beyond alpha-blend (mask-based, per-parameter sampling, ensemble distillation)
- Fitness functions per domain (OCR accuracy, latency, coding task pass@k, reasoning depth/score)
- Persistent weight repositories per generation with rollback and A/B runners
- Advanced mutation schedules (annealed noise, novelty/curiosity-driven exploration)
- Multi-parent hybridization and species niches; tournament selection and elitism
- Distributed evaluation with checkpointing and failure recovery
- Full DeepSeek-OCR API integration and GPU-accelerated pre/postprocessing

## Core AS-FDVM Features

- Backend: backend/asfdvm.py
- Categories: exploration, exploitation, innovation, stabilization, adaptation
- Agent lifecycle: spawn, mutate, retire; topic drift tracking and hints
- Adaptive search: simple scoring by fitness/interactions (placeholder for semantic search)
- Graph/status: nodes/edges grouped by category and generation; category stats and recent drift
- Flask routes (backward compatible):
  - POST /categorize { text }
  - POST /tag { content, context? }
  - POST /spawn { category?, parent_id? }
  - GET  /graph
  - GET  /status

- Frontend updates
  - ChatPane.jsx: category bubbles, seamless categorization after each message, drift hints, Dev/User toggle
  - GraphPane.jsx: group-by Category or Generation using backend /graph
  - MetricsPane.jsx: category evolution and recent drift from /status
  - ControlPane.jsx: lifecycle operations (spawn by category), mode togglea
