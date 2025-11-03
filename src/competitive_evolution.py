import os
import time
from openai import OpenAI
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from src.utils import Solution, Task, Neo4jLineageTracker
from src.production_fitness import ProductionFitnessEvaluator
# Import DeepSeek-OCR agent
from src.deepseek_ocr import DeepSeekOCRAgent

# Configuration
R1_ENDPOINT = os.getenv("R1_ENDPOINT", "http://localhost:8001/v1")
QWEN_ENDPOINT = os.getenv("QWEN_ENDPOINT", "http://localhost:8002/v1")
# DeepSeek-OCR endpoint configuration
# Note: DeepSeek-OCR uses a different API pattern (REST API for image processing)
# rather than OpenAI-compatible chat endpoints
DEEPSEEK_OCR_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
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
# Add DeepSeek-OCR health metric
vllm_deepseek_ocr_health = Gauge('vllm_deepseek_ocr_health', 'Health status of DeepSeek-OCR endpoint (1=healthy, 0=unhealthy)', registry=registry)
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
    """Main orchestration function for competitive evolution.
    
    This function now supports three competitive agents:
    1. DeepSeek-R1 (reasoning and coding)
    2. Qwen2.5-Coder (coding specialization)
    3. DeepSeek-OCR (NEW: OCR and document understanding)
    """
    print("Initializing Competitive Evolution System...")
    print("Agents: R1, Qwen2.5-Coder, DeepSeek-OCR")
    
    # Initialize OpenAI clients for both endpoints
    r1_client = OpenAI(base_url=R1_ENDPOINT, api_key="dummy-key")
    qwen_client = OpenAI(base_url=QWEN_ENDPOINT, api_key="dummy-key")
    
    # Initialize DeepSeek-OCR agent
    # TODO: Integrate OCR agent into competitive evaluation loop
    # For OCR tasks, the agent processes images and extracts structured data
    # This can be compared against R1/Qwen's vision capabilities
    ocr_agent = DeepSeekOCRAgent(api_key=DEEPSEEK_OCR_API_KEY)
    print(f"DeepSeek-OCR agent initialized: {ocr_agent.model}")
    
    # Initialize Neo4j lineage tracker
    lineage_tracker = Neo4jLineageTracker()
    
    # Initialize fitness evaluator
    fitness_evaluator = ProductionFitnessEvaluator()
    
    # Define task for cyber DFIR domain
    task = Task(
        name="ransomware_detection",
        domain="cyber_dfir",
        description="Analyze system logs and detect ransomware activity patterns",
        test_cases=[
            {"input": "sample_logs.txt", "expected": "ransomware_detected"},
        ]
    )
    
    # TODO: For OCR-specific tasks, define image-based tasks
    # Example OCR task structure:
    # ocr_task = Task(
    #     name="document_extraction",
    #     domain="ocr",
    #     description="Extract structured data from invoice images",
    #     test_cases=[
    #         {"input": "invoice_001.png", "expected": {"total": 1234.56, "vendor": "Example Corp"}},
    #     ]
    # )
    
    print(f"\nTask: {task.name}")
    print(f"Domain: {task.domain}")
    
    # Main evolution loop
    generation = 0
    max_generations = 10
    
    while generation < max_generations:
        print(f"\n{'='*60}")
        print(f"Generation {generation}")
        print(f"{'='*60}")
        
        generation_count.set(generation)
        
        # R1 Solution Generation
        print("\n[R1] Generating solution...")
        r1_start = time.time()
        try:
            r1_response = r1_client.chat.completions.create(
                model="deepseek-ai/DeepSeek-R1",
                messages=[
                    {"role": "system", "content": "You are a cybersecurity expert."},
                    {"role": "user", "content": task.description}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            r1_latency = (time.time() - r1_start) * 1000
            r1_text = r1_response.choices[0].message.content
            r1_parsed = parse_response(r1_text)
            print(f"[R1] Generated solution in {r1_latency:.2f}ms")
            inference_latency_ms.labels(model='r1', generation=generation).set(r1_latency)
        except Exception as e:
            print(f"[R1] Error: {e}")
            r1_parsed = {'code': '', 'reasoning': str(e)}
            r1_latency = 0
        
        # Qwen Solution Generation
        print("\n[Qwen] Generating solution...")
        qwen_start = time.time()
        try:
            qwen_response = qwen_client.chat.completions.create(
                model="Qwen/Qwen2.5-Coder-32B-Instruct",
                messages=[
                    {"role": "system", "content": "You are a cybersecurity expert."},
                    {"role": "user", "content": task.description}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            qwen_latency = (time.time() - qwen_start) * 1000
            qwen_text = qwen_response.choices[0].message.content
            qwen_parsed = parse_response(qwen_text)
            print(f"[Qwen] Generated solution in {qwen_latency:.2f}ms")
            inference_latency_ms.labels(model='qwen', generation=generation).set(qwen_latency)
        except Exception as e:
            print(f"[Qwen] Error: {e}")
            qwen_parsed = {'code': '', 'reasoning': str(e)}
            qwen_latency = 0
        
        # DeepSeek-OCR Processing
        # TODO: Integrate OCR agent into competitive loop for vision/OCR tasks
        # For now, we demonstrate basic OCR agent invocation
        print("\n[DeepSeek-OCR] Processing (placeholder)...")
        ocr_start = time.time()
        try:
            # Example: If task involves images, process with OCR agent
            # ocr_result = ocr_agent.process_image(
            #     image_path=task.test_cases[0]["input"],
            #     prompt=task.description
            # )
            ocr_result = {
                "status": "ready_for_integration",
                "note": "OCR agent available for image-based tasks",
                "capabilities": ["document_extraction", "invoice_parsing", "text_recognition"]
            }
            ocr_latency = (time.time() - ocr_start) * 1000
            print(f"[DeepSeek-OCR] Status: {ocr_result['status']}")
            print(f"[DeepSeek-OCR] Capabilities: {', '.join(ocr_result['capabilities'])}")
            inference_latency_ms.labels(model='deepseek-ocr', generation=generation).set(ocr_latency)
        except Exception as e:
            print(f"[DeepSeek-OCR] Error: {e}")
            ocr_result = {'status': 'error', 'error': str(e)}
        
        # Fitness Evaluation
        print("\n--- Fitness Evaluation ---")
        
        # Create Solution objects
        r1_solution = Solution(
            code=r1_parsed['code'],
            reasoning=r1_parsed['reasoning'],
            model="deepseek-r1",
            generation=generation
        )
        
        qwen_solution = Solution(
            code=qwen_parsed['code'],
            reasoning=qwen_parsed['reasoning'],
            model="qwen2.5-coder",
            generation=generation
        )
        
        # Evaluate fitness
        r1_fitness = fitness_evaluator.evaluate(r1_solution, task)
        qwen_fitness = fitness_evaluator.evaluate(qwen_solution, task)
        
        print(f"R1 Fitness: {r1_fitness:.4f}")
        print(f"Qwen Fitness: {qwen_fitness:.4f}")
        
        # Record metrics
        shinka_fitness.labels(model='r1', generation=generation).set(r1_fitness)
        shinka_fitness.labels(model='qwen', generation=generation).set(qwen_fitness)
        
        # Track lineage
        lineage_tracker.record_solution(r1_solution, task, r1_fitness)
        lineage_tracker.record_solution(qwen_solution, task, qwen_fitness)
        
        # Push metrics to Prometheus
        try:
            push_to_gateway(PROMETHEUS_GATEWAY, job='evoagent', registry=registry)
        except Exception as e:
            print(f"Warning: Failed to push metrics: {e}")
        
        generation += 1
        time.sleep(1)  # Brief pause between generations
    
    print("\n" + "="*60)
    print("Evolution Complete!")
    print(f"Total Generations: {generation}")
    print("="*60)
    
    # Display OCR agent statistics
    print("\n[DeepSeek-OCR Agent Statistics]")
    ocr_stats = ocr_agent.get_stats()
    for key, value in ocr_stats.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    main()
