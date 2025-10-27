# Competitive Evolution POC

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Description

A production-ready competitive evolution framework that pits **DeepSeek-R1** against **Qwen2.5-Coder** in a dual-pool evolutionary system. This framework combines modern LLM inference with comprehensive observability, graph-based lineage tracking, and production-grade fitness evaluation to evolve AI-generated code solutions.

Inspired by **Sakana AI's evolutionary frameworks** and adaptive reasoning approaches, this system leverages evolutionary computation principles to discover emergent capabilities across multiple domains. The architecture supports Sakana-style model merging and evolution workflows, enabling automated discovery of optimal solutions through competitive selection pressure.

New: Multi-domain knowledge support (code, behavior, physics, society, etc.) enables cross-domain learning and exploration while preserving backward compatibility with existing code pools and features.

## Key Features

- **Dual-Pool Competitive Evolution**: Two separate evolutionary pools (DeepSeek-R1 vs Qwen2.5-Coder) compete and cross-pollinate to find optimal solutions
- **Sakana-Inspired Evolution**: Evolutionary computation framework designed to support Sakana AI-style model evolution and adaptive reasoning workflows
- **Real-Time Grafana Monitoring**: Live dashboards for fitness metrics, generation progress, mutation rates, and system health
- **Neo4j Lineage Tracking**: Graph database tracking of evolutionary relationships, mutations, and ancestor chains
- **Production-Grade Fitness Evaluation**: Sandboxed code execution with resource limits, timeout protection, and comprehensive test suites
- **Efficient vLLM Inference**: High-throughput LLM serving with batching, quantization, and GPU optimization
- **Scalable Architecture**: Distributed task queue with Celery, PostgreSQL persistence, and horizontal scaling support
- **Multi-domain entities and cross-domain links**: Entities now carry a domain/category and can link across domains for transfer of knowledge
- **Human-in-the-Loop Workflow**: Interactive review and selection capabilities for guided evolution

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

## Multi-Domain Entities and Cross-Domain Learning

The core entity model (src/utils.py) now includes a domain property for both Task and Solution (default: "code" for backward compatibility). The Neo4j schema has been updated with:

- Unique constraints on ids and indexes on Solution.domain and Task.domain
- Migration helper to backfill domain for existing nodes
- Cross-domain linking via typed relationships (e.g., INFLUENCES, ALIGNED_WITH)

### New/Updated API Endpoints (backend/app.py)

- POST /api/entities/task: create a Task with optional domain
- POST /api/entities/solution: create a Solution with optional domain, link to parents and task
- POST /api/entities/link: link entities across domains with a custom relationship and attributes
- GET /api/entities/query/best?task_type=&domain=&limit=: query top solutions with optional domain filter
- GET /api/entities/query/lineage/:solution_id?depth=: retrieve lineage with domains
- GET /api/entities/query/pool_stats?pool=&domain=: pool stats optionally filtered by domain
- POST /api/entities/migrate/default_domain: backfill default domain on existing nodes

All new endpoints are additive; existing endpoints remain unchanged and behavior defaults to the "code" domain if unspecified.

## Backward Compatibility

All existing functionality is preserved:
- Existing code-domain solutions and tasks continue to work without modification
- Default domain="code" ensures seamless operation with legacy data
- All original API endpoints maintain their behavior
- Neo4j migration path provided for existing deployments

## Configuration

See `.env.example` for configuration options:
- LLM model paths and API settings
- Database connection strings (PostgreSQL, Neo4j)
- Resource limits and timeout configurations
- Monitoring and observability settings
- Domain-specific evolution parameters

## Sakana AI Integration

This framework is designed to integrate with Sakana AI's evolutionary model discovery approaches. The architecture supports:

- Model weight evolution and merging workflows
- Adaptive reasoning pattern discovery
- Cross-domain knowledge transfer
- Automated capability emergence through selection pressure

For Sakana-specific integration details, see [docs/sakana.md](docs/sakana.md).

## Contributing

Wanna help out or contribute in any way? Let us know.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
