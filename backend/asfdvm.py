"""AS-FDVM (Adaptive Search - Fractal Darwinian Virtual Machines) Implementation

Implements categories, adaptive search, agent lifecycle, and topic drift logic.
"""

import uuid
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import random
import math

# AS-FDVM Categories
CATEGORIES = [
    "exploration",
    "exploitation",
    "innovation",
    "stabilization",
    "adaptation"
]

class Agent:
    """Represents an agent with AS-FDVM properties"""
    def __init__(self, agent_id: str = None, category: str = None, parent_id: str = None, generation: int = 0):
        self.id = agent_id or str(uuid.uuid4())
        self.category = category or random.choice(CATEGORIES)
        self.parent_id = parent_id
        self.generation = generation
        self.fitness = random.uniform(0.3, 0.9)
        self.created_at = time.time()
        self.topic_vector = [random.uniform(-1, 1) for _ in range(8)]  # 8-dimensional topic space
        self.drift_velocity = [random.uniform(-0.1, 0.1) for _ in range(8)]
        self.state = "active"  # active, dormant, retired
        self.interactions = 0
        self.mutations = 0
        
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "category": self.category,
            "parent_id": self.parent_id,
            "generation": self.generation,
            "fitness": self.fitness,
            "created_at": self.created_at,
            "topic_vector": self.topic_vector,
            "drift_velocity": self.drift_velocity,
            "state": self.state,
            "interactions": self.interactions,
            "mutations": self.mutations
        }

class ASFDVMEngine:
    """Core AS-FDVM engine for categorization, search, and lifecycle management"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.category_stats = {cat: {"count": 0, "avg_fitness": 0.0} for cat in CATEGORIES}
        self.topic_drift_history = []
        self.interaction_log = []
        self.mode = "dev"  # dev or user
        
    def categorize_message(self, message: str) -> Tuple[str, float]:
        """Categorize a message into an AS-FDVM category
        
        Uses dummy logic for demonstration. In production, this would use ML models.
        """
        # Dummy categorization based on keywords
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["new", "create", "explore", "try", "discover"]):
            category = "exploration"
            confidence = 0.85
        elif any(word in message_lower for word in ["improve", "optimize", "refine", "better"]):
            category = "exploitation"
            confidence = 0.82
        elif any(word in message_lower for word in ["innovate", "novel", "unique", "revolutionary"]):
            category = "innovation"
            confidence = 0.88
        elif any(word in message_lower for word in ["stable", "maintain", "keep", "preserve"]):
            category = "stabilization"
            confidence = 0.79
        elif any(word in message_lower for word in ["adapt", "change", "adjust", "modify"]):
            category = "adaptation"
            confidence = 0.83
        else:
            # Default to exploration with lower confidence
            category = "exploration"
            confidence = 0.60
            
        return category, confidence
    
    def tag_content(self, content: str, context: Dict = None) -> List[str]:
        """Generate tags for content based on AS-FDVM principles
        
        Uses dummy logic. In production, this would use NLP/ML.
        """
        tags = []
        content_lower = content.lower()
        
        # Extract topic-related tags
        tag_keywords = {
            "performance": ["fast", "slow", "speed", "optimize"],
            "quality": ["good", "bad", "quality", "excellent"],
            "complexity": ["complex", "simple", "complicated", "easy"],
            "novelty": ["new", "novel", "unique", "original"],
            "stability": ["stable", "unstable", "reliable", "consistent"]
        }
        
        for tag, keywords in tag_keywords.items():
            if any(kw in content_lower for kw in keywords):
                tags.append(tag)
        
        # Add category-based tags
        if context and "category" in context:
            tags.append(f"category:{context['category']}")
            
        return tags
    
    def calculate_topic_drift(self, agent: Agent, new_vector: List[float]) -> Dict:
        """Calculate topic drift for an agent"""
        # Calculate Euclidean distance between vectors
        drift_magnitude = math.sqrt(sum((a - b) ** 2 for a, b in zip(agent.topic_vector, new_vector)))
        
        # Update drift velocity (exponential moving average)
        alpha = 0.3
        for i in range(len(agent.drift_velocity)):
            delta = new_vector[i] - agent.topic_vector[i]
            agent.drift_velocity[i] = alpha * delta + (1 - alpha) * agent.drift_velocity[i]
        
        # Determine drift type
        avg_velocity = sum(abs(v) for v in agent.drift_velocity) / len(agent.drift_velocity)
        if avg_velocity > 0.3:
            drift_type = "rapid"
        elif avg_velocity > 0.1:
            drift_type = "moderate"
        else:
            drift_type = "slow"
        
        drift_info = {
            "magnitude": drift_magnitude,
            "type": drift_type,
            "velocity": agent.drift_velocity,
            "hint": self._generate_drift_hint(drift_type, agent.category)
        }
        
        # Update agent's topic vector
        agent.topic_vector = new_vector
        
        # Log drift
        self.topic_drift_history.append({
            "agent_id": agent.id,
            "timestamp": time.time(),
            "drift": drift_info
        })
        
        return drift_info
    
    def _generate_drift_hint(self, drift_type: str, category: str) -> str:
        """Generate a hint message based on drift type and category"""
        hints = {
            "rapid": [
                f"Rapid topic shift detected in {category} domain",
                f"High velocity change - consider spawning new {category} agent",
                f"Topic divergence accelerating in {category}"
            ],
            "moderate": [
                f"Steady evolution in {category} focus",
                f"Moderate drift - {category} agent adapting",
                f"Topic gradually shifting in {category} space"
            ],
            "slow": [
                f"Stable {category} trajectory",
                f"Minimal drift - {category} agent converging",
                f"Topic consistency in {category}"
            ]
        }
        return random.choice(hints.get(drift_type, ["Topic drift detected"]))
    
    def spawn_agent(self, category: str = None, parent_id: str = None) -> Agent:
        """Spawn a new agent with optional parent"""
        generation = 0
        if parent_id and parent_id in self.agents:
            parent = self.agents[parent_id]
            generation = parent.generation + 1
            # Inherit category with small mutation chance
            if category is None:
                category = parent.category if random.random() > 0.2 else random.choice(CATEGORIES)
        
        agent = Agent(category=category, parent_id=parent_id, generation=generation)
        self.agents[agent.id] = agent
        
        # Update category stats
        self._update_category_stats()
        
        return agent
    
    def retire_agent(self, agent_id: str) -> bool:
        """Retire an agent (change state to retired)"""
        if agent_id in self.agents:
            self.agents[agent_id].state = "retired"
            self._update_category_stats()
            return True
        return False
    
    def mutate_agent(self, agent_id: str, mutation_type: str = "random") -> Optional[Agent]:
        """Mutate an agent's properties"""
        if agent_id not in self.agents:
            return None
        
        agent = self.agents[agent_id]
        agent.mutations += 1
        
        if mutation_type == "category":
            # Change category
            old_category = agent.category
            agent.category = random.choice([c for c in CATEGORIES if c != old_category])
        elif mutation_type == "fitness":
            # Adjust fitness
            agent.fitness = max(0.1, min(1.0, agent.fitness + random.uniform(-0.2, 0.2)))
        elif mutation_type == "topic":
            # Shift topic vector
            for i in range(len(agent.topic_vector)):
                agent.topic_vector[i] += random.uniform(-0.3, 0.3)
                agent.topic_vector[i] = max(-1, min(1, agent.topic_vector[i]))
        else:
            # Random mutation
            mutation_types = ["category", "fitness", "topic"]
            return self.mutate_agent(agent_id, random.choice(mutation_types))
        
        self._update_category_stats()
        return agent
    
    def adaptive_search(self, query: str, category_filter: List[str] = None) -> List[Agent]:
        """Perform adaptive search across agents
        
        Uses dummy logic. In production, this would use semantic search.
        """
        # Filter by category if specified
        candidates = [
            agent for agent in self.agents.values()
            if agent.state == "active" and (not category_filter or agent.category in category_filter)
        ]
        
        # Dummy scoring based on fitness and interactions
        scored_agents = []
        for agent in candidates:
            # Simple scoring: fitness + interaction bonus
            score = agent.fitness + (agent.interactions * 0.01)
            scored_agents.append((score, agent))
        
        # Sort by score descending
        scored_agents.sort(reverse=True, key=lambda x: x[0])
        
        # Return top agents
        return [agent for score, agent in scored_agents[:10]]
    
    def _update_category_stats(self):
        """Update category statistics"""
        # Reset counts
        for cat in CATEGORIES:
            self.category_stats[cat] = {"count": 0, "fitness_sum": 0.0}
        
        # Count active agents by category
        for agent in self.agents.values():
            if agent.state == "active":
                self.category_stats[agent.category]["count"] += 1
                self.category_stats[agent.category]["fitness_sum"] += agent.fitness
        
        # Calculate averages
        for cat in CATEGORIES:
            count = self.category_stats[cat]["count"]
            if count > 0:
                self.category_stats[cat]["avg_fitness"] = self.category_stats[cat]["fitness_sum"] / count
            else:
                self.category_stats[cat]["avg_fitness"] = 0.0
    
    def get_graph_data(self) -> Dict:
        """Generate graph data organized by category and generation"""
        nodes = []
        edges = []
        
        for agent in self.agents.values():
            nodes.append({
                "id": agent.id,
                "category": agent.category,
                "generation": agent.generation,
                "fitness": agent.fitness,
                "state": agent.state
            })
            
            if agent.parent_id:
                edges.append({
                    "source": agent.parent_id,
                    "target": agent.id
                })
        
        # Group by category
        by_category = {cat: [] for cat in CATEGORIES}
        for node in nodes:
            by_category[node["category"]].append(node)
        
        # Group by generation
        by_generation = {}
        for node in nodes:
            gen = node["generation"]
            if gen not in by_generation:
                by_generation[gen] = []
            by_generation[gen].append(node)
        
        return {
            "nodes": nodes,
            "edges": edges,
            "by_category": by_category,
            "by_generation": by_generation
        }
    
    def get_status(self) -> Dict:
        """Get current system status"""
        active_agents = [a for a in self.agents.values() if a.state == "active"]
        
        return {
            "mode": self.mode,
            "total_agents": len(self.agents),
            "active_agents": len(active_agents),
            "category_stats": self.category_stats,
            "recent_drift": self.topic_drift_history[-5:] if self.topic_drift_history else [],
            "timestamp": time.time()
        }

# Global engine instance
engine = ASFDVMEngine()

# Initialize with some seed agents
for _ in range(3):
    engine.spawn_agent()
