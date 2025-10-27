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

## Phase 2 — Caretaker UI

Phase 2 extends the basic monitoring capabilities with an advanced interactive caretaker interface featuring real-time code editing, enhanced visualization, comprehensive logging, and automated maintenance tools.

### Phase 2 Architecture

Phase 2 introduces a modern full-stack architecture:

- **Frontend** (`frontend/`): React-based UI with Monaco Editor, built with Vite
  - Real-time dashboard for monitoring evolution progress
  - Interactive code editor with syntax highlighting and IntelliSense
  - Neo4j graph visualization and tagging interface
  - Live system logs with filtering and search
  - Responsive design with modern UI components

- **Backend API** (`backend/`): Flask-based REST API
  - RESTful endpoints for code management and evolution control
  - Neo4j integration for lineage tracking and tagging
  - Real-time log streaming via WebSocket
  - Entity CRUD operations for evolutionary artifacts
  - Authentication and authorization support

- **Automation Scripts** (`scripts/`): Maintenance and management utilities
  - `neo4j_topic_tagger.py`: Automated tagging script for categorizing evolution entities
    - Tags high-performing entities (fitness > 0.8)
    - Identifies veteran entities (generation >= 10)
    - Flags isolated entities for potential optimization
    - Runs as part of scheduled maintenance workflows

- **Docker Integration**: Updated `docker-compose.yml` includes:
  - Frontend service (React + Vite dev server on port 5173)
  - Backend API service (Flask on port 5000)
  - All existing Phase 1 services (Neo4j, Prometheus, Grafana, etc.)

### Phase 2 Features

- **Code Editor with Monaco**: Integrated Monaco Editor (VS Code engine) for viewing and editing evolved code with syntax highlighting, IntelliSense, and error detection
- **Neo4j Tagging Interface**: Interactive UI for tagging and categorizing evolutionary nodes, managing lineage relationships, and exploring graph-based ancestry
- **Real-time System Logs**: Live log streaming with filtering, severity levels, and search capabilities for monitoring evolution execution and debugging
- **Automated Maintenance**: Python scripts for routine Neo4j database maintenance and entity classification

### Activation Instructions

To enable Phase 2 features:

1. **Frontend Configuration**: Edit `frontend/src/config.js` and set `PHASE_2_ENABLED: true`

2. **Deploy Phase 2 Services**:
   ```bash
   # Start all services including Phase 2 UI and API
   docker-compose up -d frontend backend
   ```

3. **Access the Caretaker UI**:
   - Navigate to http://localhost:5173 in your browser
   - The UI will connect to the backend API at http://localhost:5000

4. **Run Automated Tagging** (optional):
   ```bash
   # Execute the Neo4j topic tagging script
   python scripts/neo4j_topic_tagger.py
   
   # Or run via Docker
   docker-compose exec backend python /app/scripts/neo4j_topic_tagger.py
   ```

### Phase 2 Directory Structure

```
competitive-evolution-poc/
├── frontend/              # React UI application
│   ├── src/
│   │   ├── components/     # Phase 1 components
│   │   ├── components-phase2/  # Enhanced Phase 2 components
│   │   ├── services/       # API integration layer
│   │   ├── App.jsx         # Main application
│   │   └── config.js       # Configuration (phase toggles)
│   ├── Dockerfile
│   └── package.json
├── backend/               # Flask REST API
│   ├── phase2/            # Phase 2 specific routes
│   ├── app.py             # Main API server
│   ├── Dockerfile
│   └── requirements.txt
├── scripts/               # Automation utilities
│   └── neo4j_topic_tagger.py  # Automated entity tagging
├── docker-compose.yml     # Updated with frontend & backend services
└── README.md              # This file
```

### Notes

- Phase 2 components are clearly separated from core engine files (`src/competitive_evolution.py` remains unchanged)
- All Phase 2 additions are optional and can be disabled by setting `PHASE_2_ENABLED: false`
- The backend API is designed to be stateless and horizontally scalable
- Frontend development server runs on port 5173; production builds can be served via Nginx

## Development

### Running Tests

```bash
# Run all tests
make test

# Run specific test suite
pytest tests/test_competitive_evolution.py
```

### Contributing

Contributions are welcome! Please follow the existing code style and include tests for new features.

## License

MIT License - see LICENSE file for details
