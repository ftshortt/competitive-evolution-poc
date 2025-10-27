import uuid
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import json

class Agent:
    """Represents a single agent with lifecycle, traits, and relationships."""
    
    def __init__(self, parent=None, traits=None, agent_id=None, name=None):
        self.id = agent_id or str(uuid.uuid4())
        self.parent = parent
        self.children = []
        self.traits = traits or {}
        self.alive = True
        self.birth_time = time.time()
        self.death_time = None
        self.fitness = 0.0
        self.generation = 0 if parent is None else parent.generation + 1
        self.name = name or f"Agent-{self.id[:8]}"
        self.interaction_count = 0
        self.topic_history = []
        self.domain_specialization = traits.get('domain', 'general') if traits else 'general'
        
    def spawn_child(self, traits_override=None, name=None):
        """Spawn a child agent with inherited and modified traits."""
        child_traits = self.traits.copy()
        if traits_override:
            child_traits.update(traits_override)
        
        child = Agent(parent=self, traits=child_traits, name=name)
        self.children.append(child)
        return child
    
    def die(self):
        """Mark agent as no longer alive."""
        self.alive = False
        self.death_time = time.time()
    
    def update_fitness(self, new_fitness):
        """Update the agent's fitness score."""
        self.fitness = new_fitness
    
    def log_interaction(self, topic=None):
        """Log an interaction and optionally a topic."""
        self.interaction_count += 1
        if topic:
            self.topic_history.append({
                'topic': topic,
                'timestamp': time.time()
            })
    
    def to_dict(self):
        """Convert agent to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent.id if self.parent else None,
            'traits': self.traits,
            'alive': self.alive,
            'birth_time': self.birth_time,
            'death_time': self.death_time,
            'fitness': self.fitness,
            'generation': self.generation,
            'interaction_count': self.interaction_count,
            'domain_specialization': self.domain_specialization,
            'children_ids': [child.id for child in self.children]
        }


class LifecycleManager:
    """Manages the lifecycle of all agents, including spawning, tracking, and retirement."""
    
    def __init__(self, neo4j_driver=None):
        self.agents = {}  # Dictionary of agent_id -> Agent
        self.neo4j_driver = neo4j_driver
        self.root_agents = []  # Track root (parentless) agents
        self.topic_categories = {}  # Track emergent topic categories
        
    def create_root_agent(self, traits=None, name="Root Agent"):
        """Create a root agent with no parent."""
        agent = Agent(parent=None, traits=traits, name=name)
        self.agents[agent.id] = agent
        self.root_agents.append(agent)
        
        if self.neo4j_driver:
            self._persist_agent_to_neo4j(agent)
        
        return agent
    
    def spawn_child_agent(self, parent_id, traits_override=None, name=None):
        """Spawn a child from a parent agent."""
        parent = self.agents.get(parent_id)
        if not parent:
            raise ValueError(f"Parent agent {parent_id} not found")
        
        if not parent.alive:
            raise ValueError(f"Parent agent {parent_id} is not alive")
        
        child = parent.spawn_child(traits_override, name)
        self.agents[child.id] = child
        
        if self.neo4j_driver:
            self._persist_agent_to_neo4j(child)
            self._persist_relationship_to_neo4j(parent, child)
        
        return child
    
    def retire_agent(self, agent_id):
        """Retire an agent (mark as dead)."""
        agent = self.agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        agent.die()
        
        if self.neo4j_driver:
            self._update_agent_in_neo4j(agent)
        
        return agent
    
    def get_live_agents(self):
        """Get all currently alive agents."""
        return [agent for agent in self.agents.values() if agent.alive]
    
    def get_agent(self, agent_id):
        """Get a specific agent by ID."""
        return self.agents.get(agent_id)
    
    def get_agent_lineage(self, agent_id):
        """Get the full lineage (ancestors and descendants) of an agent."""
        agent = self.agents.get(agent_id)
        if not agent:
            return None
        
        # Get ancestors
        ancestors = []
        current = agent.parent
        while current:
            ancestors.append(current.to_dict())
            current = current.parent
        
        # Get descendants (recursive)
        def get_descendants(a):
            desc = []
            for child in a.children:
                desc.append(child.to_dict())
                desc.extend(get_descendants(child))
            return desc
        
        descendants = get_descendants(agent)
        
        return {
            'agent': agent.to_dict(),
            'ancestors': ancestors,
            'descendants': descendants
        }
    
    def get_family_tree(self, agent_id):
        """Get the family tree for visualization."""
        lineage = self.get_agent_lineage(agent_id)
        if not lineage:
            return None
        
        # Build tree structure for visualization
        tree_nodes = []
        tree_edges = []
        
        # Add ancestors
        for ancestor in lineage['ancestors']:
            tree_nodes.append(ancestor)
            if ancestor['parent_id']:
                tree_edges.append({
                    'source': ancestor['parent_id'],
                    'target': ancestor['id']
                })
        
        # Add current agent
        tree_nodes.append(lineage['agent'])
        if lineage['agent']['parent_id']:
            tree_edges.append({
                'source': lineage['agent']['parent_id'],
                'target': lineage['agent']['id']
            })
        
        # Add descendants
        for descendant in lineage['descendants']:
            tree_nodes.append(descendant)
            if descendant['parent_id']:
                tree_edges.append({
                    'source': descendant['parent_id'],
                    'target': descendant['id']
                })
        
        return {
            'nodes': tree_nodes,
            'edges': tree_edges
        }
    
    def evaluate_fitness(self, agent_id, evaluation_data):
        """Evaluate and update agent fitness based on performance data."""
        agent = self.agents.get(agent_id)
        if not agent:
            return None
        
        # Calculate fitness based on multiple factors
        interaction_score = min(evaluation_data.get('interaction_count', 0) / 100.0, 1.0)
        accuracy_score = evaluation_data.get('accuracy', 0.5)
        domain_score = evaluation_data.get('domain_expertise', 0.5)
        
        # Weighted fitness calculation
        fitness = (interaction_score * 0.3 + accuracy_score * 0.4 + domain_score * 0.3)
        agent.update_fitness(fitness)
        
        if self.neo4j_driver:
            self._update_agent_in_neo4j(agent)
        
        return fitness
    
    def auto_retire_low_fitness_agents(self, threshold=0.2):
        """Automatically retire agents with fitness below threshold."""
        retired = []
        for agent in self.get_live_agents():
            if agent.fitness < threshold and agent.generation > 0:  # Don't retire root agents
                agent.die()
                retired.append(agent.id)
                if self.neo4j_driver:
                    self._update_agent_in_neo4j(agent)
        return retired
    
    def log_topic_drift(self, agent_id, topic, category=None):
        """Log topic drift for analysis and potential category creation."""
        agent = self.agents.get(agent_id)
        if not agent:
            return
        
        agent.log_interaction(topic)
        
        # Track topic frequency
        if topic not in self.topic_categories:
            self.topic_categories[topic] = {
                'count': 0,
                'category': category,
                'first_seen': time.time()
            }
        self.topic_categories[topic]['count'] += 1
        
        # Auto-categorize if topic appears frequently
        if self.topic_categories[topic]['count'] >= 5 and not self.topic_categories[topic]['category']:
            self.topic_categories[topic]['category'] = 'auto-generated'
    
    def get_metrics(self):
        """Get overall system metrics."""
        live_agents = self.get_live_agents()
        all_agents = list(self.agents.values())
        
        total_live = len(live_agents)
        avg_fitness = sum(a.fitness for a in live_agents) / total_live if total_live > 0 else 0
        max_generation = max((a.generation for a in all_agents), default=0)
        
        generation_distribution = {}
        for agent in live_agents:
            gen = agent.generation
            generation_distribution[gen] = generation_distribution.get(gen, 0) + 1
        
        return {
            'total_agents': len(all_agents),
            'live_agents': total_live,
            'dead_agents': len(all_agents) - total_live,
            'average_fitness': avg_fitness,
            'max_generation': max_generation,
            'generation_distribution': generation_distribution,
            'root_agents': len(self.root_agents),
            'topic_categories': len(self.topic_categories)
        }
    
    def _persist_agent_to_neo4j(self, agent):
        """Persist agent to Neo4j database."""
        if not self.neo4j_driver:
            return
        
        query = """
        CREATE (a:Agent {
            id: $id,
            name: $name,
            traits: $traits,
            alive: $alive,
            birth_time: $birth_time,
            fitness: $fitness,
            generation: $generation,
            domain_specialization: $domain_specialization
        })
        """
        
        with self.neo4j_driver.session() as session:
            session.run(query, 
                id=agent.id,
                name=agent.name,
                traits=json.dumps(agent.traits),
                alive=agent.alive,
                birth_time=agent.birth_time,
                fitness=agent.fitness,
                generation=agent.generation,
                domain_specialization=agent.domain_specialization
            )
    
    def _persist_relationship_to_neo4j(self, parent, child):
        """Persist parent-child relationship to Neo4j."""
        if not self.neo4j_driver:
            return
        
        query = """
        MATCH (p:Agent {id: $parent_id})
        MATCH (c:Agent {id: $child_id})
        CREATE (p)-[:SPAWNED]->(c)
        """
        
        with self.neo4j_driver.session() as session:
            session.run(query, parent_id=parent.id, child_id=child.id)
    
    def _update_agent_in_neo4j(self, agent):
        """Update agent in Neo4j database."""
        if not self.neo4j_driver:
            return
        
        query = """
        MATCH (a:Agent {id: $id})
        SET a.alive = $alive,
            a.fitness = $fitness,
            a.death_time = $death_time
        """
        
        with self.neo4j_driver.session() as session:
            session.run(query,
                id=agent.id,
                alive=agent.alive,
                fitness=agent.fitness,
                death_time=agent.death_time
            )
