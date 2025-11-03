# EvoAgent

## Overview
EvoAgent is an evolutionary AI system that enables agents to adapt, compete, and improve through natural selection principles. Built on the AS-FDVM (Adaptive Search - Fractal Darwinian Virtual Machines) architecture, EvoAgent creates a competitive ecosystem where multiple AI agents evolve solutions through mutation, adaptation, and competitive evolution.

## Unique Possibilities and Summary

**EvoAgent represents the next step in evolutionary agent frameworks.** Powered by AZR's robust, battle-tested pipelines, EvoAgent doesn't just train agents—it evolves them in a competitive, adaptive ecosystem that mirrors natural selection.

### Why EvoAgent?

- **Evolving Graph Memory**: Agents maintain dynamic, evolving knowledge graphs that adapt and grow with experience, enabling persistent learning and contextual intelligence that improves over time.

- **Competitive Agent Mixing**: Multiple agents compete and collaborate simultaneously, with the strongest solutions naturally emerging through fitness-based selection. This competitive pressure drives continuous improvement without manual intervention.

- **Lineage Tracking**: Every evolved agent carries a complete genealogy—trace back through generations to understand how breakthrough capabilities emerged, enabling reproducible research and transparent evolution.

- **Emergent Collaborative Intelligence**: Watch as agents spontaneously develop cooperative strategies, share learned behaviors, and collectively solve problems beyond individual capability—true swarm intelligence in action.

- **Production-Ready Infrastructure**: Built on proven FSDP+QLoRA foundations from AZR, with robust checkpointing, artifact management, and distributed training out of the box. Go from experimentation to production seamlessly.

### The Vision

EvoAgent transforms AI development from manual iteration to guided evolution. Instead of training one model at a time, you create conditions for intelligence to emerge naturally through competition, adaptation, and selection. The result? Agents that continuously improve, adapt to new challenges, and develop capabilities you never explicitly programmed.

**Join us in building the future of adaptive AI.** Whether you're a researcher exploring evolutionary algorithms, an engineer seeking production-grade agent systems, or a contributor passionate about emergent intelligence—EvoAgent provides the framework to push boundaries.

## AZR-derived Best Practices and New Features
The following capabilities were integrated by adapting Absolute-Zero-Reasoner (AZR) best practices to EvoAgent.

### 1) Robust FSDP+QLoRA wrapper for fine-tuning (OCR, R1, Qwen)
- Freeze → Inject → Wrap sequence to ensure compatibility between FSDP and QLoRA
- 4-bit quantization with nf4 + bfloat16 compute for memory efficiency
- Frequent checkpointing and safe adapter-only saves
- Distributed initialization with LOCAL_RANK handling

Code:
- src/fsdp_qlora_wrapper.py
  
- create_ocr_agent()
  
- create_r1_agent()
  
- create_qwen_agent()

Usage example (single node, multi-GPU):
```bash
torchrun --nproc_per_node=NUM_GPUS -m src.agent_orchestrator
```

Environment:
```bash
export EVO_AGENT=qwen   # or r1, ocr
```

### 2) Cyclical/auto-stopping orchestration pipeline for agent evolution
- Cyclic training/evolution loops with:
  
- Auto-stop on max steps or max runtime
  
- Checkpoint every 2 steps with validation hooks
  
- Strict run separation via run_id (each run in ./runs/<timestamp>)

- Consolidation hook after cycles to produce exportable artifacts

Code:
- src/agent_orchestrator.py (entrypoint)

### 3) Artifact-safe merging and validation utilities for evolved agents
- Validate LoRA checkpoints before merge
- Merge base + adapters into standalone artifact (PEFT merge_and_unload)
- Write CHECKSUMS.txt for reproducibility and audit

Code:
- src/artifact_merger.py

### 4) Strict experiment data separation and checkpointing
- All runs stored under ./runs/<run_id>/
- Checkpoints saved under ./runs/<run_id>/ckpts/checkpoint-<step>
- metadata.json per checkpoint for validation and lineage tracking
- Designed to be resilient to interruptions and dataset exhaustion

## Quickstart
1) Install requirements
```bash
pip install -r requirements.txt
```

2) Choose agent and launch orchestrator
```bash
export EVO_AGENT=qwen  # or r1, ocr
torchrun --nproc_per_node=2 -m src.agent_orchestrator
```

3) Output locations
- Checkpoints: ./runs/<run_id>/ckpts/
- Final artifact (after consolidation): see src/artifact_merger.py utilities

## Extending
- Plug in your training step in EvoAgentOrchestrator.train_step()
- Integrate production fitness/validation in validate_checkpoint() and/or src/production_fitness.py
- Expand consolidation to call a full merge/export pipeline suitable for deployment

## Notes
- These integrations were adapted from the AZR SINGLE_GPU pipeline and consolidation scripts with adjustments for EvoAgent's modular architecture.
- Ensure CUDA + NCCL are configured for FSDP. Prefer bfloat16-capable GPUs.
