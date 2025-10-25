"""Integration tests for the competitive evolution system.

These tests require external services to be running:
- Neo4j database (for lineage tracking)
- vLLM endpoints at localhost:8001 and localhost:8002 (for LLM inference)
- Prometheus Pushgateway at localhost:9091 (for metrics)

Run with: pytest -m integration
"""

import pytest
import time
import requests
from src.task import Task
from src.fitness_evaluator import ProductionFitnessEvaluator
from src.solution import Solution
from src.lineage_tracker import Neo4jLineageTracker


@pytest.mark.integration
def test_end_to_end_smoke_test():
    """End-to-end smoke test of the core workflow.
    
    This test verifies that the basic pipeline works:
    1. Create a task
    2. Create a fitness evaluator
    3. Create a solution
    4. Evaluate fitness
    5. Store in lineage database
    6. Query to verify storage
    
    Requires Neo4j to be running.
    """
    # Create a task for the cyber_dfir domain
    task = Task(domain="cyber_dfir")
    
    # Create a production fitness evaluator
    evaluator = ProductionFitnessEvaluator()
    
    # Create a simple solution
    solution = Solution(code='print("hello")')
    
    # Evaluate fitness
    fitness = evaluator.evaluate(solution, task)
    
    # Assert fitness is positive
    assert fitness > 0, f"Expected fitness > 0, got {fitness}"
    
    # Create lineage tracker and add solution to database
    tracker = Neo4jLineageTracker()
    tracker.add_solution(solution, fitness, task)
    
    # Query to verify the solution exists
    results = tracker.query_solutions(domain="cyber_dfir")
    assert len(results) > 0, "Solution was not stored in database"
    
    # Close the tracker connection
    tracker.close()


@pytest.mark.integration
@pytest.mark.skipif(
    not all([
        requests.get("http://localhost:8001/health", timeout=1).status_code == 200,
        requests.get("http://localhost:8002/health", timeout=1).status_code == 200
    ]) if True else False,
    reason="vLLM endpoints not available"
)
def test_vllm_endpoints_health():
    """Test that vLLM endpoints are responding correctly.
    
    This test verifies that both vLLM inference endpoints are healthy.
    Skips if endpoints are not available.
    
    Requires vLLM services at localhost:8001 and localhost:8002.
    """
    # Check first endpoint
    response1 = requests.get("http://localhost:8001/health", timeout=5)
    assert response1.status_code == 200, "vLLM endpoint 1 is not healthy"
    
    # Check second endpoint
    response2 = requests.get("http://localhost:8002/health", timeout=5)
    assert response2.status_code == 200, "vLLM endpoint 2 is not healthy"


@pytest.mark.integration
def test_prometheus_pushgateway():
    """Test pushing metrics to Prometheus Pushgateway.
    
    This test verifies that the Prometheus Pushgateway is accepting metrics.
    Attempts to push a test metric and verifies no errors occur.
    
    Requires Prometheus Pushgateway at localhost:9091.
    """
    # Prepare test metric data
    metric_data = (
        '# TYPE test_metric counter\n'
        'test_metric{job="test",instance="test_instance"} 42\n'
    )
    
    # Push to Pushgateway
    url = "http://localhost:9091/metrics/job/test_integration"
    response = requests.post(
        url,
        data=metric_data,
        headers={'Content-Type': 'text/plain'}
    )
    
    # Verify no errors (Pushgateway returns 200 or 202 on success)
    assert response.status_code in [200, 202], (
        f"Failed to push metric: {response.status_code} - {response.text}"
    )
