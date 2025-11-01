#!/bin/bash
set -euo pipefail

# 🚀 Deploying EvoAgent...
echo "🚀 Deploying EvoAgent..."
echo ""

# Check for dependencies
echo "Checking dependencies..."
missing_deps=()
if ! command -v docker &> /dev/null; then
    missing_deps+=("docker")
fi
if ! command -v python3 &> /dev/null; then
    missing_deps+=("python3")
fi
if ! command -v nvidia-smi &> /dev/null; then
    missing_deps+=("nvidia-smi")
fi
if ! command -v curl &> /dev/null; then
    missing_deps+=("curl")
fi

if [ ${#missing_deps[@]} -ne 0 ]; then
    echo "Error: Missing dependencies: ${missing_deps[*]}"
    exit 1
fi
echo "All dependencies found ✓"
echo ""

# Create/activate Python venv
echo "Setting up Python environment..."
if [ ! -d "venv" ]; then
    echo "Creating new virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing requirements..."
    pip install -r requirements.txt
else
    echo "Using existing virtual environment..."
    source venv/bin/activate
fi
echo "Python environment ready ✓"
echo ""

# Start Docker services
echo "Starting Docker services..."
docker-compose up -d
echo "Waiting 10 seconds for services to initialize..."
sleep 10
echo "Docker services started ✓"
echo ""

# Deploy vLLM pools
echo "Deploying vLLM pools..."
./deploy/deploy_pools.sh
echo "Waiting 15 seconds for vLLM pools to initialize..."
sleep 15
echo "vLLM pools deployed ✓"
echo ""

# Health checks
echo "Performing health checks..."
for i in {1..30}; do
    echo "Health check attempt $i/30..."
    
    health1=false
    health2=false
    
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        health1=true
    fi
    if curl -s http://localhost:8002/health > /dev/null 2>&1; then
        health2=true
    fi
    
    if [ "$health1" = true ] && [ "$health2" = true ]; then
        echo "All services healthy ✓"
        break
    fi
    
    if [ $i -eq 30 ]; then
        echo "Warning: Not all services are healthy after 30 attempts"
        echo "  Pool 1 (8001): $health1"
        echo "  Pool 2 (8002): $health2"
        echo "Continuing anyway..."
    fi
    
    sleep 2
done
echo ""

# Import Grafana dashboard
echo "Importing Grafana dashboard..."
for i in {1..10}; do
    if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
        echo "Grafana is ready ✓"
        break
    fi
    echo "Waiting for Grafana... ($i/10)"
    sleep 3
done

echo "Importing dashboard JSON..."
curl -X POST \
  http://admin:admin@localhost:3000/api/dashboards/db \
  -H 'Content-Type: application/json' \
  -d @infra/grafana_dashboard.json

echo ""
echo "🎉 EvoAgent Deployment Complete!"
echo ""
echo "Access points:"
echo "  - Neo4j Browser: http://localhost:7474"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3000 (admin/admin)"
echo "  - vLLM Pool 1 (DeepSeek-R1): http://localhost:8001"
echo "  - vLLM Pool 2 (Qwen2.5-Coder): http://localhost:8002"
echo ""
echo "To start the evolution system:"
echo "  make run"
echo ""
