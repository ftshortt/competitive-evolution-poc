#!/bin/bash
set -euo pipefail

# Deploy vLLM pools for competitive evolution framework
# Usage: ./deploy_pools.sh [deepseek_model_path] [qwen_model_path]

# Default model paths
DEEPSEEK_MODEL="${1:-./models/deepseek-r1-7b}"
QWEN_MODEL="${2:-./models/qwen2.5-coder-14b}"

# Create logs directory if it doesn't exist
mkdir -p logs

echo "Starting vLLM deployment..."
echo "DeepSeek model: $DEEPSEEK_MODEL"
echo "Qwen model: $QWEN_MODEL"

# Function to check service health
check_health() {
    local port=$1
    local service_name=$2
    
    if curl -f -s "http://localhost:${port}/health" > /dev/null 2>&1; then
        echo "✓ ${service_name} is healthy on port ${port}"
        return 0
    else
        echo "✗ ${service_name} health check failed on port ${port}"
        return 1
    fi
}

# Deploy DeepSeek-R1 pool (port 8001, 0.35 GPU utilization, AWQ quantization)
echo "Deploying DeepSeek-R1 pool on port 8001..."
vllm serve "${DEEPSEEK_MODEL}" \
    --port 8001 \
    --gpu-memory-utilization 0.35 \
    --quantization awq \
    > logs/pool_r1.log 2>&1 &

# Save PID
echo $! > logs/pool_r1.pid
echo "DeepSeek-R1 PID: $(cat logs/pool_r1.pid)"

# Wait for service to start
echo "Waiting 8 seconds for DeepSeek-R1 to initialize..."
sleep 8

# Health check for DeepSeek-R1
if ! check_health 8001 "DeepSeek-R1"; then
    echo "Error: DeepSeek-R1 failed to start properly"
    exit 1
fi

# Deploy Qwen2.5-Coder pool (port 8002, 0.55 GPU utilization, AWQ quantization)
echo "Deploying Qwen2.5-Coder pool on port 8002..."
vllm serve "${QWEN_MODEL}" \
    --port 8002 \
    --gpu-memory-utilization 0.55 \
    --quantization awq \
    > logs/pool_qwen.log 2>&1 &

# Save PID
echo $! > logs/pool_qwen.pid
echo "Qwen2.5-Coder PID: $(cat logs/pool_qwen.pid)"

# Wait for service to start
echo "Waiting 8 seconds for Qwen2.5-Coder to initialize..."
sleep 8

# Health check for Qwen2.5-Coder
if ! check_health 8002 "Qwen2.5-Coder"; then
    echo "Error: Qwen2.5-Coder failed to start properly"
    exit 1
fi

echo "✓ All vLLM pools deployed successfully!"
echo "DeepSeek-R1: http://localhost:8001 (PID: $(cat logs/pool_r1.pid))"
echo "Qwen2.5-Coder: http://localhost:8002 (PID: $(cat logs/pool_qwen.pid))"
echo "Logs available in logs/ directory"
