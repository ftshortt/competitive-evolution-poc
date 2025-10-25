"""Utility classes and functions for competitive evolution system."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from neo4j import GraphDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Task:
    """Represents a task/problem to be solved."""
    id: str
    task_type: str
    description: str
    test_cases: List[Dict[str, Any]] = field(default_factory=list)
    difficulty: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Solution:
    """Represents a solution to a task."""
    id: str
    code: str
    reasoning_trace: str
    fitness: float
    pool: str
    pool_trait: str
    generation: int
    task_type: str
    reasoning_steps: int
    token_cost: int
    parent_ids: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    task_id: Optional[str] = None
    execution_time: Optional[float] = None
    memory_usage: Optional[int] = None
    
    def __post_init__(self):
        """Validate solution data after initialization."""
        if self.fitness < 0 or self.fitness > 1:
            raise ValueError(f"Fitness must be between 0 and 1, got {self.fitness}")
        if self.generation < 0:
            raise ValueError(f"Generation must be non-negative, got {self.generation}")
        if self.reasoning_steps < 0:
            raise ValueError(f"Reasoning steps must be non-negative, got {self.reasoning_steps}")
        if self.token_cost < 0:
            raise ValueError(f"Token cost must be non-negative, got {self.token_cost}")


class Neo4jLineageTracker:
    """Tracks evolutionary lineage of solutions in Neo4j graph database."""
    
    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "evolution2025"):
        """Initialize Neo4j connection.
        
        Args:
            uri: Neo4j database URI
            user: Database username
            password: Database password
        """
        self.uri = uri
        self.user = user
        self.driver = None
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            logger.info(f"Connected to Neo4j at {uri}")
            self._create_constraints()
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def _create_constraints(self):
        """Create database constraints for data integrity."""
        with self.driver.session() as session:
            try:
                # Create uniqueness constraints
                session.run("CREATE CONSTRAINT solution_id IF NOT EXISTS FOR (s:Solution) REQUIRE s.id IS UNIQUE")
                session.run("CREATE CONSTRAINT task_id IF NOT EXISTS FOR (t:Task) REQUIRE t.id IS UNIQUE")
                logger.info("Database constraints created successfully")
            except Exception as e:
                logger.warning(f"Could not create constraints (may already exist): {e}")
    
    def close(self):
        """Close database connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def add_task(self, task: Task) -> bool:
        """Add a task to the database.
        
        Args:
            task: Task object to add
            
        Returns:
            True if successful, False otherwise
        """
        with self.driver.session() as session:
            try:
                query = """
                CREATE (t:Task {
                    id: $id,
                    task_type: $task_type,
                    description: $description,
                    difficulty: $difficulty,
                    timestamp: datetime($timestamp)
                })
                RETURN t
                """
                session.run(
                    query,
                    id=task.id,
                    task_type=task.task_type,
                    description=task.description,
                    difficulty=task.difficulty,
                    timestamp=task.timestamp.isoformat()
                )
                logger.info(f"Added task {task.id} to database")
                return True
            except Exception as e:
                logger.error(f"Failed to add task {task.id}: {e}")
                return False
    
    def add_solution(self, solution: Solution) -> bool:
        """Add a solution to the database and create relationships.
        
        Creates:
        - Solution node with all attributes
        - SOLVES relationship to Task (if task_id provided)
        - EVOLVED_FROM relationships to parent solutions
        - GENERATED_BY relationship to indicate generation
        
        Args:
            solution: Solution object to add
            
        Returns:
            True if successful, False otherwise
        """
        with self.driver.session() as session:
            try:
                # Create Solution node
                query = """
                CREATE (s:Solution {
                    id: $id,
                    code: $code,
                    reasoning_trace: $reasoning_trace,
                    fitness: $fitness,
                    pool: $pool,
                    pool_trait: $pool_trait,
                    generation: $generation,
                    task_type: $task_type,
                    reasoning_steps: $reasoning_steps,
                    token_cost: $token_cost,
                    timestamp: datetime($timestamp),
                    execution_time: $execution_time,
                    memory_usage: $memory_usage
                })
                RETURN s
                """
                session.run(
                    query,
                    id=solution.id,
                    code=solution.code,
                    reasoning_trace=solution.reasoning_trace,
                    fitness=solution.fitness,
                    pool=solution.pool,
                    pool_trait=solution.pool_trait,
                    generation=solution.generation,
                    task_type=solution.task_type,
                    reasoning_steps=solution.reasoning_steps,
                    token_cost=solution.token_cost,
                    timestamp=solution.timestamp.isoformat(),
                    execution_time=solution.execution_time,
                    memory_usage=solution.memory_usage
                )
                
                # Create SOLVES relationship to Task
                if solution.task_id:
                    task_query = """
                    MATCH (s:Solution {id: $solution_id})
                    MATCH (t:Task {id: $task_id})
                    CREATE (s)-[:SOLVES]->(t)
                    """
                    session.run(task_query, solution_id=solution.id, task_id=solution.task_id)
                
                # Create EVOLVED_FROM relationships to parents
                if solution.parent_ids:
                    parent_query = """
                    MATCH (s:Solution {id: $solution_id})
                    MATCH (p:Solution {id: $parent_id})
                    CREATE (s)-[:EVOLVED_FROM]->(p)
                    """
                    for parent_id in solution.parent_ids:
                        session.run(parent_query, solution_id=solution.id, parent_id=parent_id)
                
                # Create GENERATED_BY relationship (to track generation)
                gen_query = """
                MATCH (s:Solution {id: $solution_id})
                SET s.generation_metadata = $generation
                """
                session.run(gen_query, solution_id=solution.id, generation=solution.generation)
                
                logger.info(f"Added solution {solution.id} to database (gen {solution.generation}, fitness {solution.fitness:.3f})")
                return True
                
            except Exception as e:
                logger.error(f"Failed to add solution {solution.id}: {e}")
                return False
    
    def get_solution(self, solution_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a solution by ID.
        
        Args:
            solution_id: ID of the solution to retrieve
            
        Returns:
            Dictionary with solution data or None if not found
        """
        with self.driver.session() as session:
            try:
                query = """
                MATCH (s:Solution {id: $solution_id})
                RETURN s
                """
                result = session.run(query, solution_id=solution_id)
                record = result.single()
                if record:
                    return dict(record["s"])
                return None
            except Exception as e:
                logger.error(f"Failed to retrieve solution {solution_id}: {e}")
                return None
    
    def get_lineage(self, solution_id: str, depth: int = 10) -> List[Dict[str, Any]]:
        """Get evolutionary lineage of a solution.
        
        Args:
            solution_id: ID of the solution
            depth: Maximum depth to traverse (default 10)
            
        Returns:
            List of ancestor solutions in chronological order
        """
        with self.driver.session() as session:
            try:
                query = """
                MATCH path = (s:Solution {id: $solution_id})-[:EVOLVED_FROM*0..%d]->(ancestor:Solution)
                RETURN ancestor
                ORDER BY ancestor.generation ASC
                """ % depth
                result = session.run(query, solution_id=solution_id)
                return [dict(record["ancestor"]) for record in result]
            except Exception as e:
                logger.error(f"Failed to get lineage for {solution_id}: {e}")
                return []
    
    def get_best_solutions(self, task_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get best solutions by fitness.
        
        Args:
            task_type: Filter by task type (optional)
            limit: Maximum number of solutions to return
            
        Returns:
            List of top solutions ordered by fitness
        """
        with self.driver.session() as session:
            try:
                if task_type:
                    query = """
                    MATCH (s:Solution {task_type: $task_type})
                    RETURN s
                    ORDER BY s.fitness DESC
                    LIMIT $limit
                    """
                    result = session.run(query, task_type=task_type, limit=limit)
                else:
                    query = """
                    MATCH (s:Solution)
                    RETURN s
                    ORDER BY s.fitness DESC
                    LIMIT $limit
                    """
                    result = session.run(query, limit=limit)
                return [dict(record["s"]) for record in result]
            except Exception as e:
                logger.error(f"Failed to get best solutions: {e}")
                return []
    
    def get_pool_statistics(self, pool: str) -> Dict[str, Any]:
        """Get statistics for a specific pool.
        
        Args:
            pool: Pool name
            
        Returns:
            Dictionary with pool statistics
        """
        with self.driver.session() as session:
            try:
                query = """
                MATCH (s:Solution {pool: $pool})
                RETURN 
                    count(s) as solution_count,
                    avg(s.fitness) as avg_fitness,
                    max(s.fitness) as max_fitness,
                    min(s.fitness) as min_fitness,
                    avg(s.token_cost) as avg_token_cost,
                    max(s.generation) as max_generation
                """
                result = session.run(query, pool=pool)
                record = result.single()
                if record:
                    return dict(record)
                return {}
            except Exception as e:
                logger.error(f"Failed to get pool statistics for {pool}: {e}")
                return {}
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
