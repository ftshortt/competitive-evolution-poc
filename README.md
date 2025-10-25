# Competitive Evolution POC
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Description

A production-ready competitive evolution framework that pits **DeepSeek-R1** against **Qwen2.5-Coder** in a dual-pool evolutionary system. This framework combines modern LLM inference with comprehensive observability, graph-based lineage tracking, and production-grade fitness evaluation to evolve AI-generated code solutions.

## Key Features

- **Dual-Pool Competitive Evolution**: Two separate evolutionary pools (DeepSeek-R1 vs Qwen2.5-Coder) compete and cross-pollinate to find optimal solutions
- **Real-Time Grafana Monitoring**: Live dashboards for fitness metrics, generation progress, mutation rates, and system health
- **Neo4j Lineage Tracking**: Graph database tracking of evolutionary relationships, mutations, and ancestor chains
- **Production-Grade Fitness Evaluation**: Sandboxed code execution with resource limits, timeout protection, and comprehensive test suites
- **Efficient vLLM Inference**: High-throughput LLM serving with batching, quantization, and GPU optimization
- **Scalable Architecture**: Distributed task queue with Celery, PostgreSQL persistence, and horizontal scaling support

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose
- NVIDIA GPU with CUDA 12.1+
- 16GB+ VRAM recommended

### Installation

```bash
# Clone the repository
git clone https://github.com/ftshortt/competitive-evolution-poc.git
cd competitive-evolution-poc

# Install dependencies
make install

# Configure environment
cp .env.example .env
# Edit .env with your configuration (API keys, model paths, etc.)

# Deploy services
make deploy
```

### Dashboard Access

Once deployed, access the monitoring dashboards:

- **Grafana**: http://localhost:3000 (credentials: `admin` / `evolution2025`)
- **Prometheus**: http://localhost:9090
- **Neo4j Browser**: http://localhost:7474 (credentials: `neo4j` / `evolution2025`)

### Monitoring and Management

```bash
# Monitor logs in real-time
make monitor

# Stop all services
make stop
```

## Phase 2 - Enhanced Caretaker Interface (Optional)

Phase 2 extends the basic monitoring capabilities with an advanced interactive caretaker interface featuring real-time code editing, enhanced visualization, and comprehensive logging.

### Phase 2 Features

- **Code Editor with Monaco**: Integrated Monaco Editor (VS Code engine) for viewing and editing evolved code with syntax highlighting, IntelliSense, and error detection
- **Neo4j Tagging Interface**: Interactive UI for tagging and categorizing evolutionary nodes, managing lineage relationships, and exploring graph-based ancestry
- **Real-time System Logs**: Live log streaming with filtering, severity levels, and search capabilities for monitoring evolution execution and debugging

### Activation Instructions

To enable Phase 2 features:

1. **Frontend Configuration**: Edit `frontend/src/config.js` and set `PHASE_2_ENABLED: true`
2. **Backend Environment**: Add `PHASE_2_ENABLED=true` to your `.env` file
3. **Restart Services**: Run `make deploy` to apply changes

For detailed integration instructions, architecture diagrams, and API documentation, see [docs/PHASE2_INTEGRATION.md](docs/PHASE2_INTEGRATION.md).

### Feature Overview

| Feature | Phase 1 | Phase 2 |
|---------|---------|----------|
| Evolution Monitoring | ✓ Grafana Dashboards | ✓ Enhanced Real-time Visualization |
| Code Viewing | ✓ Basic Text Display | ✓ Monaco Editor with Syntax Highlighting |
| Lineage Tracking | ✓ Neo4j Backend | ✓ Interactive Tagging & Exploration UI |
| System Logs | ✓ Docker Logs | ✓ Live Streaming with Filters |
| Code Editing | ✗ | ✓ In-browser Editing & Validation |
| Node Tagging | ✗ | ✓ Custom Tags & Categories |

### Recommendations

**We strongly recommend testing Phase 1 functionality first** to verify that core evolution, fitness evaluation, and monitoring are working correctly before enabling Phase 2 features. Phase 2 adds UI complexity that is best explored once you're familiar with the underlying evolutionary system.

## Project Structure

```
competitive-evolution-poc/
├── src/
│   ├── evolution/          # Core evolution engine
│   ├── fitness/            # Fitness evaluation and sandboxing
│   ├── inference/          # vLLM model serving
│   ├── monitoring/         # Prometheus metrics and Grafana dashboards
│   └── storage/            # Neo4j and PostgreSQL adapters
├── tests/                  # Unit and integration tests
├── docs/                   # Additional documentation
├── infra/                  # Infrastructure and deployment configs
├── deploy/                 # Deployment scripts and Dockerfiles
└── Makefile               # Build and deployment automation
```

## Architecture

The system consists of several key components:

1. **Evolution Engine**: Manages dual-pool genetic algorithms, crossover operations, and mutation strategies
2. **Fitness Evaluator**: Executes and scores generated code in isolated sandboxes with comprehensive test suites
3. **Model Inference**: vLLM-powered serving of DeepSeek-R1 and Qwen2.5-Coder with efficient batching
4. **Storage Layer**: PostgreSQL for persistence, Neo4j for lineage graphs
5. **Task Queue**: Celery-based distributed processing for parallel evolution
6. **Observability**: Prometheus metrics collection with Grafana visualization

## Configuration

Key configuration options in `.env`:

```bash
# Model Configuration
DEEPSEEK_MODEL_PATH=/models/deepseek-r1
QWEN_MODEL_PATH=/models/qwen2.5-coder

# Evolution Parameters
POPULATION_SIZE=50
GENERATIONS=100
MUTATION_RATE=0.2
CROSSOVER_RATE=0.7

# Infrastructure
POSTGRES_HOST=postgres
NEO4J_HOST=neo4j
REDIS_HOST=redis

# Phase 2 (Optional)
PHASE_2_ENABLED=false
```

## Development

```bash
# Run tests
make test

# Run linting
make lint

# Format code
make format

# Build Docker images locally
make build
```

## Troubleshooting

### GPU Not Detected

Ensure NVIDIA drivers and CUDA toolkit are properly installed:

```bash
nvidia-smi
docker run --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### Out of Memory Errors

Reduce batch size or enable model quantization in `.env`:

```bash
VLLM_QUANTIZATION=awq
VLLM_MAX_BATCH_SIZE=8
```

### Connection Issues

Verify all services are running:

```bash
docker-compose ps
```

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [vLLM](https://github.com/vllm-project/vllm) for efficient LLM inference
- Monitoring powered by [Grafana](https://grafana.com/) and [Prometheus](https://prometheus.io/)
- Lineage tracking with [Neo4j](https://neo4j.com/)
- Task orchestration via [Celery](https://docs.celeryproject.org/)

## Citation

If you use this framework in your research, please cite:

```bibtex
@software{competitive_evolution_poc,
  title = {Competitive Evolution POC: Dual-Pool LLM Evolution Framework},
  author = {ftshortt},
  year = {2025},
  url = {https://github.com/ftshortt/competitive-evolution-poc}
}
```
