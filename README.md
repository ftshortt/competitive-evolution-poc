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
├── docker-compose.yml      # Service orchestration
├── Makefile                # Development and deployment commands
└── requirements.txt        # Python dependencies
```

## Development

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-coverage
```

### Code Quality

```bash
# Lint code
make lint

# Format code
make format

# Type checking
make typecheck
```

## Architecture Overview

### Dual-Pool Evolution System

```
┌─────────────────────────────────────────────────────────────┐
│                     Evolution Coordinator                    │
└───────────────┬─────────────────────────────────┬───────────┘
                │                                 │
     ┌──────────▼──────────┐           ┌─────────▼──────────┐
     │   DeepSeek-R1 Pool  │           │ Qwen2.5-Coder Pool │
     │  (Reasoning Focus)  │◄─────────►│  (Coding Focus)    │
     └──────────┬──────────┘           └─────────┬──────────┘
                │         Cross-Pollination        │
                └──────────────┬──────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Fitness Evaluator  │
                    │    (Sandboxed)      │
                    └──────────┬──────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
        ┌───────▼──────┐ ┌────▼────┐ ┌──────▼──────┐
        │   Grafana    │ │  Neo4j  │ │ PostgreSQL  │
        │ (Monitoring) │ │(Lineage)│ │(Persistence)│
        └──────────────┘ └─────────┘ └─────────────┘
```

The system maintains two separate evolution pools, each optimized for different LLM strengths:
- **DeepSeek-R1**: Excels at reasoning and problem decomposition
- **Qwen2.5-Coder**: Optimized for code generation and syntax

Periodic cross-pollination transfers top performers between pools, combining reasoning depth with coding proficiency.

## Scaling Guide

For production deployment on multi-GPU clusters (4-8x H100), see the comprehensive scaling guide:

📖 **[docs/SCALING_GUIDE.md](docs/SCALING_GUIDE.md)**

Covers:
- Multi-GPU model parallelism
- Distributed task queue configuration
- Database sharding and replication
- Load balancing strategies
- Performance benchmarks

## Documentation

- [Architecture Details](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)
- [Configuration Guide](docs/CONFIGURATION.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## Citation

If you use this framework in your research, please cite:

```bibtex
@software{competitive_evolution_poc,
  title = {Competitive Evolution POC: A Dual-Pool LLM Evolution Framework},
  author = {ftshortt},
  year = {2025},
  url = {https://github.com/ftshortt/competitive-evolution-poc},
  note = {Production-ready framework for competitive AI code evolution}
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built with**: Python • vLLM • Neo4j • PostgreSQL • Grafana • Prometheus • Docker
