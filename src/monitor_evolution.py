import time
import psutil
import subprocess
from neo4j import GraphDatabase
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

# Configuration
NEO4J_URI = "bolt://localhost:7687"
PUSHGATEWAY = "localhost:9091"

# Prometheus metrics setup
registry = CollectorRegistry()
gpu_memory_mb = Gauge('gpu_memory_mb', 'GPU Memory Usage in MB', registry=registry)
gpu_utilization_percent = Gauge('gpu_utilization_percent', 'GPU Utilization Percentage', registry=registry)
cpu_utilization_percent = Gauge('cpu_utilization_percent', 'CPU Utilization Percentage', registry=registry)
cpu_memory_mb = Gauge('cpu_memory_mb', 'CPU Memory Usage in MB', registry=registry)

def get_system_usage():
    """Poll system metrics including CPU and GPU usage."""
    metrics = {}
    
    # CPU metrics
    metrics['cpu_utilization'] = psutil.cpu_percent(interval=1)
    metrics['cpu_memory'] = psutil.virtual_memory().used / (1024 * 1024)  # Convert to MB
    
    # GPU metrics via nvidia-smi
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=memory.used,utilization.gpu', '--format=csv,noheader,nounits'],
            capture_output=True,
            text=True,
            check=True
        )
        gpu_data = result.stdout.strip().split(',')
        metrics['gpu_memory'] = float(gpu_data[0])
        metrics['gpu_utilization'] = float(gpu_data[1])
    except (subprocess.CalledProcessError, FileNotFoundError, IndexError):
        # nvidia-smi not available or failed
        metrics['gpu_memory'] = 0.0
        metrics['gpu_utilization'] = 0.0
    
    return metrics

def push_system_metrics():
    """Push system metrics to Prometheus pushgateway."""
    metrics = get_system_usage()
    
    # Update Prometheus gauges
    cpu_utilization_percent.set(metrics['cpu_utilization'])
    cpu_memory_mb.set(metrics['cpu_memory'])
    gpu_memory_mb.set(metrics['gpu_memory'])
    gpu_utilization_percent.set(metrics['gpu_utilization'])
    
    # Push to gateway
    try:
        push_to_gateway(PUSHGATEWAY, job='evolution_monitor', registry=registry)
    except Exception as e:
        print(f"Failed to push metrics: {e}")

def monitor_evolution_loop():
    """Monitor evolution progress with system metrics."""
    driver = GraphDatabase.driver(NEO4J_URI)
    
    try:
        while True:
            # Push system metrics
            push_system_metrics()
            
            # Query Neo4j for evolution progress
            try:
                with driver.session() as session:
                    result = session.run(
                        "MATCH (s:Species) RETURN MAX(s.fitness) as max_fitness, MAX(s.generation) as max_generation"
                    )
                    record = result.single()
                    if record:
                        max_fitness = record['max_fitness']
                        max_generation = record['max_generation']
                        print(f"Current Evolution Progress - Generation: {max_generation}, Max Fitness: {max_fitness}")
            except Exception as e:
                print(f"Failed to query Neo4j: {e}")
            
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")
    finally:
        driver.close()

if __name__ == "__main__":
    monitor_evolution_loop()
