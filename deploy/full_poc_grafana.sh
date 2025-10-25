#!/bin/bash

set -euo pipefail

# 🚀 Deploying PoC...
echo "🚀 Deploying PoC..."
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
        echo "All endpoints healthy ✓"
        break
    fi
    
    if [ $i -eq 30 ]; then
        echo "Warning: Health checks did not complete in time"
        echo "localhost:8001/health: $health1"
        echo "localhost:8002/health: $health2"
    fi
    
    sleep 2
done

echo ""
echo "========================================"
echo "🎉 PoC Deployment Complete!"
echo "========================================"
echo ""
echo "Access your services:"
echo ""
echo "📊 Grafana:    http://localhost:3000"
echo "   Username: admin"
echo "   Password: evolution2025"
echo ""
echo "📈 Prometheus: http://localhost:9090"
echo ""
echo "🔍 Neo4j:      http://localhost:7474"
echo "   Username: neo4j"
echo "   Password: evolution2025"
echo ""
echo "Services are running in the background."
echo "Use 'docker-compose logs -f' to view logs."
echo "Use './deploy/shutdown_pools.sh && docker-compose down' to stop."
echo "========================================"
