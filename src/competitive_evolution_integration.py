"""Competitive Evolution Integration for DeepSeek-R1 and Qwen2.5-Coder.

This module demonstrates how the new evolvable agent wrappers
(EvolvableDeepSeekR1 and EvolvableQwenCoder) integrate with the
competitive evolution framework.

The agents are now fully implemented and ready to compete alongside
DeepSeek-OCR in evolutionary optimization.
"""

from src.deepseek_r1 import EvolvableDeepSeekR1
from src.qwen_coder import EvolvableQwenCoder
from src.deepseek_ocr import DeepSeekOCRAgent
import random
from typing import List, Dict, Any


def merge_weights(weights1: Dict[str, Any], weights2: Dict[str, Any], alpha: float = 0.5) -> Dict[str, Any]:
    """
    Merge two weight dictionaries using alpha blending.
    
    Args:
        weights1: First agent's weights
        weights2: Second agent's weights
        alpha: Blending factor (0.0 = all weights1, 1.0 = all weights2)
        
    Returns:
        Merged weights dictionary
    """
    merged = {}
    for key in weights1:
        if isinstance(weights1[key], (int, float)) and isinstance(weights2.get(key), (int, float)):
            merged[key] = alpha * weights1[key] + (1 - alpha) * weights2[key]
        else:
            # For categorical parameters, randomly choose
            merged[key] = random.choice([weights1[key], weights2.get(key, weights1[key])])
    return merged


def create_population(api_key: str, population_size: int = 10) -> Dict[str, List]:
    """
    Initialize a population of evolvable agents.
    
    Args:
        api_key: API key for agent initialization
        population_size: Number of agents per type to create
        
    Returns:
        Dictionary with agent type as key and list of agents as value
    """
    population = {
        'r1_agents': [],
        'qwen_agents': [],
    }
    
    # Create R1 agents with varying configurations
    for i in range(population_size):
        agent = EvolvableDeepSeekR1(
            api_key=api_key,
            temperature=random.uniform(0.5, 1.5),
            max_tokens=random.randint(2000, 8000),
            reasoning_effort=random.choice(['low', 'medium', 'high'])
        )
        population['r1_agents'].append(agent)
    
    # Create Qwen agents with varying configurations
    for i in range(population_size):
        agent = EvolvableQwenCoder(
            api_key=api_key,
            temperature=random.uniform(0.3, 1.0),
            max_tokens=random.randint(1000, 4096),
            top_p=random.uniform(0.8, 1.0),
            top_k=random.randint(20, 80)
        )
        population['qwen_agents'].append(agent)
    
    return population


def evolve_generation(population: Dict[str, List], fitness_scores: Dict[str, List[float]], 
                     mutation_rate: float = 0.1, crossover_rate: float = 0.5) -> Dict[str, List]:
    """
    Evolve the population to the next generation using selection, crossover, and mutation.
    
    Args:
        population: Current population of agents
        fitness_scores: Fitness scores for each agent
        mutation_rate: Probability and magnitude of mutations
        crossover_rate: Probability of crossover vs cloning
        
    Returns:
        New generation of agents
    """
    new_population = {
        'r1_agents': [],
        'qwen_agents': [],
    }
    
    # Evolve R1 agents
    r1_agents = population['r1_agents']
    r1_fitness = fitness_scores['r1_fitness']
    
    # Sort by fitness (descending)
    sorted_indices = sorted(range(len(r1_fitness)), key=lambda i: r1_fitness[i], reverse=True)
    
    # Keep top performers (elitism)
    elite_count = max(1, len(r1_agents) // 5)
    for idx in sorted_indices[:elite_count]:
        new_population['r1_agents'].append(r1_agents[idx])
    
    # Create offspring through selection and crossover/mutation
    while len(new_population['r1_agents']) < len(r1_agents):
        # Tournament selection
        parent1_idx = max(random.sample(range(len(r1_agents)), 3), key=lambda i: r1_fitness[i])
        parent2_idx = max(random.sample(range(len(r1_agents)), 3), key=lambda i: r1_fitness[i])
        
        parent1 = r1_agents[parent1_idx]
        parent2 = r1_agents[parent2_idx]
        
        if random.random() < crossover_rate:
            # Crossover: merge weights
            child = EvolvableDeepSeekR1(
                api_key=parent1.api_key,
                base_url=parent1.base_url
            )
            merged_weights = merge_weights(
                parent1.get_weights(),
                parent2.get_weights(),
                alpha=random.uniform(0.3, 0.7)
            )
            child.set_weights(merged_weights)
        else:
            # Clone parent1
            child = EvolvableDeepSeekR1(
                api_key=parent1.api_key,
                base_url=parent1.base_url
            )
            child.set_weights(parent1.get_weights())
        
        # Mutation
        if random.random() < mutation_rate:
            child = child.mutate(mutation_rate=mutation_rate)
        
        new_population['r1_agents'].append(child)
    
    # Similar evolution for Qwen agents
    qwen_agents = population['qwen_agents']
    qwen_fitness = fitness_scores['qwen_fitness']
    
    sorted_indices = sorted(range(len(qwen_fitness)), key=lambda i: qwen_fitness[i], reverse=True)
    elite_count = max(1, len(qwen_agents) // 5)
    
    for idx in sorted_indices[:elite_count]:
        new_population['qwen_agents'].append(qwen_agents[idx])
    
    while len(new_population['qwen_agents']) < len(qwen_agents):
        parent1_idx = max(random.sample(range(len(qwen_agents)), 3), key=lambda i: qwen_fitness[i])
        parent2_idx = max(random.sample(range(len(qwen_agents)), 3), key=lambda i: qwen_fitness[i])
        
        parent1 = qwen_agents[parent1_idx]
        parent2 = qwen_agents[parent2_idx]
        
        if random.random() < crossover_rate:
            # Use built-in crossover method
            child = parent1.crossover(parent2)
        else:
            child = EvolvableQwenCoder(
                api_key=parent1.api_key,
                base_url=parent1.base_url
            )
            child.set_weights(parent1.get_weights())
        
        if random.random() < mutation_rate:
            child = child.mutate(mutation_rate=mutation_rate)
        
        new_population['qwen_agents'].append(child)
    
    return new_population


def run_competitive_evolution(
    api_key: str,
    num_generations: int = 10,
    population_size: int = 10,
    tasks: List[Any] = None
):
    """
    Run competitive evolution with DeepSeek-R1 and Qwen2.5-Coder agents.
    
    Args:
        api_key: API key for agent initialization
        num_generations: Number of evolutionary generations
        population_size: Size of population per agent type
        tasks: List of tasks for fitness evaluation
    """
    if tasks is None:
        tasks = []  # User should provide domain-specific tasks
    
    # Initialize population
    population = create_population(api_key, population_size)
    
    for generation in range(num_generations):
        print(f"\n=== Generation {generation + 1} ===")
        
        # Evaluate fitness (stub - user should implement domain-specific evaluation)
        fitness_scores = {
            'r1_fitness': [random.random() for _ in range(len(population['r1_agents']))],
            'qwen_fitness': [random.random() for _ in range(len(population['qwen_agents']))],
        }
        
        # Log best agents
        best_r1_idx = max(range(len(fitness_scores['r1_fitness'])), 
                         key=lambda i: fitness_scores['r1_fitness'][i])
        best_qwen_idx = max(range(len(fitness_scores['qwen_fitness'])), 
                           key=lambda i: fitness_scores['qwen_fitness'][i])
        
        print(f"Best R1 fitness: {fitness_scores['r1_fitness'][best_r1_idx]:.4f}")
        print(f"Best R1 weights: {population['r1_agents'][best_r1_idx].get_weights()}")
        print(f"Best Qwen fitness: {fitness_scores['qwen_fitness'][best_qwen_idx]:.4f}")
        print(f"Best Qwen weights: {population['qwen_agents'][best_qwen_idx].get_weights()}")
        
        # Evolve to next generation
        if generation < num_generations - 1:
            population = evolve_generation(
                population, 
                fitness_scores,
                mutation_rate=0.1,
                crossover_rate=0.5
            )
    
    # Return best agents
    best_r1 = population['r1_agents'][best_r1_idx]
    best_qwen = population['qwen_agents'][best_qwen_idx]
    
    return {
        'best_r1_agent': best_r1,
        'best_qwen_agent': best_qwen,
        'final_population': population
    }


if __name__ == "__main__":
    # Example usage
    import os
    
    api_key = os.getenv("DEEPSEEK_API_KEY", "your-api-key-here")
    
    print("Starting competitive evolution with DeepSeek-R1 and Qwen2.5-Coder...")
    print("This demonstrates the integration of evolvable agent wrappers.")
    print("The agents support get/set/update_weights for evolutionary optimization.\n")
    
    results = run_competitive_evolution(
        api_key=api_key,
        num_generations=5,
        population_size=8
    )
    
    print("\n=== Evolution Complete ===")
    print(f"Best R1 agent weights: {results['best_r1_agent'].get_weights()}")
    print(f"Best Qwen agent weights: {results['best_qwen_agent'].get_weights()}")
    
    # Save best agents
    results['best_r1_agent'].save('best_r1_agent.json')
    results['best_qwen_agent'].save('best_qwen_agent.json')
    print("\nBest agents saved to disk.")
w
