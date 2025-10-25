import os
import time
from openai import OpenAI
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

from src.utils import Solution, Task, Neo4jLineageTracker
from src.production_fitness import ProductionFitnessEvaluator

# Configuration
R1_ENDPOINT = os.getenv("R1_ENDPOINT", "http://localhost:8001/v1")
QWEN_ENDPOINT = os.getenv("QWEN_ENDPOINT", "http://localhost:8002/v1")
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
inference_latency_ms = Gauge('inference_latency_ms', 'Inference latency in milliseconds', ['model', 'generation'], registry=registry)

def parse_response(response_text: str) -> dict:
    """Parse model response to extract code blocks and reasoning.
    
    Args:
        response_text: Raw text output from the model
        
    Returns:
        Dictionary containing 'code' and 'reasoning' keys
    """
    result = {'code': '', 'reasoning': ''}
    
    # Extract code blocks (```...```)
    if '```' in response_text:
        parts = response_text.split('```')
        for i, part in enumerate(parts):
            if i % 2 == 1:  # Odd indices are code blocks
                # Remove language identifier if present
                lines = part.strip().split('\n')
                if lines and lines[0].strip() in ['python', 'py', 'bash', 'sh']:
                    result['code'] = '\n'.join(lines[1:])
                else:
                    result['code'] = part.strip()
                break
    
    # Extract reasoning (everything outside code blocks)
    reasoning_parts = []
    parts = response_text.split('```')
    for i, part in enumerate(parts):
        if i % 2 == 0:  # Even indices are reasoning
            reasoning_parts.append(part.strip())
    result['reasoning'] = ' '.join(reasoning_parts).strip()
    
    return result

def main():
    """Main orchestration function for competitive evolution."""
    print("Initializing Competitive Evolution System...")
    
    # Initialize OpenAI clients for both endpoints
    r1_client = OpenAI(base_url=R1_ENDPOINT, api_key="dummy-key")
    qwen_client = OpenAI(base_url=QWEN_ENDPOINT, api_key="dummy-key")
    
    # Initialize Neo4j lineage tracker
    lineage_tracker = Neo4jLineageTracker()
    
    # Initialize fitness evaluator
    fitness_evaluator = ProductionFitnessEvaluator()
    
    # Define task for cyber DFIR domain
    task = Task(
        name="ransomware_detection",
        domain="cyber_dfir",
        description="Detect and analyze ransomware patterns in system logs and file activities",
        constraints="Must handle large log files efficiently and identify encryption patterns"
    )
    
    print(f"Task: {task.name} in domain {task.domain}")
    print(f"Description: {task.description}")
    print(f"Starting evolution loop for 50 generations...\n")
    
    # Evolution loop for 50 generations
    for generation in range(1, 51):
        print(f"=== Generation {generation} ===")
        generation_count.set(generation)
        
        # Call R1 model
        print("Calling R1 model...")
        start_time = time.time()
        try:
            r1_response = r1_client.chat.completions.create(
                model="deepseek-r1",
                messages=[{
                    "role": "user",
                    "content": f"Task: {task.description}\nConstraints: {task.constraints}\nProvide a solution with code and reasoning."
                }],
                max_tokens=2048,
                temperature=0.7
            )
            r1_latency = (time.time() - start_time) * 1000
            r1_output = r1_response.choices[0].message.content
            r1_parsed = parse_response(r1_output)
            vllm_r1_health.set(1)
        except Exception as e:
            print(f"R1 model error: {e}")
            vllm_r1_health.set(0)
            r1_parsed = {'code': '', 'reasoning': ''}
            r1_latency = 0
        
        inference_latency_ms.labels(model='r1', generation=generation).set(r1_latency)
        
        # Create R1 solution
        r1_solution = Solution(
            model_name="deepseek-r1",
            task=task,
            code=r1_parsed['code'],
            reasoning=r1_parsed['reasoning'],
            generation=generation
        )
        
        # Evaluate R1 fitness
        print("Evaluating R1 fitness...")
        r1_fitness = fitness_evaluator.evaluate(r1_solution)
        r1_solution.fitness_score = r1_fitness
        shinka_fitness.labels(model='r1', generation=generation).set(r1_fitness)
        print(f"R1 fitness: {r1_fitness:.4f}")
        
        # Track R1 lineage
        lineage_tracker.track_solution(r1_solution)
        
        # Call Qwen model
        print("Calling Qwen model...")
        start_time = time.time()
        try:
            qwen_response = qwen_client.chat.completions.create(
                model="qwen2.5-72b",
                messages=[{
                    "role": "user",
                    "content": f"Task: {task.description}\nConstraints: {task.constraints}\nProvide a solution with code and reasoning."
                }],
                max_tokens=2048,
                temperature=0.7
            )
            qwen_latency = (time.time() - start_time) * 1000
            qwen_output = qwen_response.choices[0].message.content
            qwen_parsed = parse_response(qwen_output)
            vllm_qwen_health.set(1)
        except Exception as e:
            print(f"Qwen model error: {e}")
            vllm_qwen_health.set(0)
            qwen_parsed = {'code': '', 'reasoning': ''}
            qwen_latency = 0
        
        inference_latency_ms.labels(model='qwen', generation=generation).set(qwen_latency)
        
        # Create Qwen solution
        qwen_solution = Solution(
            model_name="qwen2.5-72b",
            task=task,
            code=qwen_parsed['code'],
            reasoning=qwen_parsed['reasoning'],
            generation=generation
        )
        
        # Evaluate Qwen fitness
        print("Evaluating Qwen fitness...")
        qwen_fitness = fitness_evaluator.evaluate(qwen_solution)
        qwen_solution.fitness_score = qwen_fitness
        shinka_fitness.labels(model='qwen', generation=generation).set(qwen_fitness)
        print(f"Qwen fitness: {qwen_fitness:.4f}")
        
        # Track Qwen lineage
        lineage_tracker.track_solution(qwen_solution)
        
        # Calculate and track performance gain
        performance_gain = abs(r1_fitness - qwen_fitness)
        dgm_performance_gain.labels(model='r1', generation=generation).set(performance_gain if r1_fitness > qwen_fitness else 0)
        dgm_performance_gain.labels(model='qwen', generation=generation).set(performance_gain if qwen_fitness > r1_fitness else 0)
        
        # Push metrics to Prometheus
        try:
            push_to_gateway(PROMETHEUS_GATEWAY, job='competitive_evolution', registry=registry)
            print("Metrics pushed to Prometheus")
        except Exception as e:
            print(f"Failed to push metrics: {e}")
        
        print(f"Generation {generation} complete\n")
        
        # Small delay between generations
        time.sleep(2)
    
    print("Evolution complete!")
    lineage_tracker.close()

if __name__ == "__main__":
    main()
