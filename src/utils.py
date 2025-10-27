"""Utility classes and functions for competitive evolution system with multi-domain support."""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from neo4j import GraphDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Backward-compatible constants
DEFAULT_DOMAIN = "code"

@dataclass
class Task:
    """Represents a task/problem to be solved."""
    id: str
    task_type: str
    description: str
    test_cases: List[Dict[str, Any]] = field(default_factory=list)
    difficulty: Optional[str] = None
    # New: domain/category for the task (e.g., code, behavior, physics, society, etc.)
    domain: str = DEFAULT_DOMAIN
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
    # New: domain/category for the solution's entity
    domain: str = DEFAULT_DOMAIN

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
        # Normalize domain to lower-case simple token
        if not self.domain:
            self.domain = DEFAULT_DOMAIN
        self.domain = str(self.domain).strip().lower()

class Neo4jLineageTracker:
    """Tracks evolutionary lineage of solutions and tasks in Neo4j graph database with cross-domain support."""

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
        """Create indexes/constraints for efficient queries and domain support."""
        with self.driver.session() as session:
            # Ensure unique ids
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:Solution) REQUIRE s.id IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (t:Task) REQUIRE t.id IS UNIQUE")
            # Common indexes for filtering
            session.run("CREATE INDEX IF NOT EXISTS FOR (s:Solution) ON (s.task_type)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (s:Solution) ON (s.pool)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (s:Solution) ON (s.domain)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (t:Task) ON (t.task_type)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (t:Task) ON (t.domain)")

    # Entity creation and migration
    def create_task(self, task: Task) -> Dict[str, Any]:
        with self.driver.session() as session:
            query = (
                "MERGE (t:Task {id: $id}) "
                "SET t.task_type = $task_type, t.description = $description, "
                "t.test_cases = $test_cases, t.difficulty = $difficulty, "
                "t.timestamp = datetime($timestamp), t.domain = $domain "
                "RETURN t"
            )
            rec = session.run(
                query,
                id=task.id,
                task_type=task.task_type,
                description=task.description,
                test_cases=task.test_cases,
                difficulty=task.difficulty,
                timestamp=task.timestamp.isoformat(),
                domain=task.domain,
            ).single()
            return dict(rec["t"]) if rec else {}

    def create_solution(self, solution: Solution) -> Dict[str, Any]:
        with self.driver.session() as session:
            query = (
                "MERGE (s:Solution {id: $id}) "
                "SET s.code = $code, s.reasoning_trace = $reasoning_trace, s.fitness = $fitness, "
                "s.pool = $pool, s.pool_trait = $pool_trait, s.generation = $generation, s.task_type = $task_type, "
                "s.reasoning_steps = $reasoning_steps, s.token_cost = $token_cost, s.timestamp = datetime($timestamp), "
                "s.task_id = $task_id, s.execution_time = $execution_time, s.memory_usage = $memory_usage, s.domain = $domain "
                "RETURN s"
            )
            rec = session.run(
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
                task_id=solution.task_id,
                execution_time=solution.execution_time,
                memory_usage=solution.memory_usage,
                domain=solution.domain,
            ).single()
            return dict(rec["s"]) if rec else {}

    def link_solution_to_task(self, solution_id: str, task_id: str):
        with self.driver.session() as session:
            session.run(
                "MATCH (s:Solution {id: $sid}), (t:Task {id: $tid}) "
                "MERGE (s)-[:SOLVES]->(t)",
                sid=solution_id,
                tid=task_id,
            )

    def link_parent(self, child_id: str, parent_id: str):
        with self.driver.session() as session:
            session.run(
                "MATCH (c:Solution {id: $cid}), (p:Solution {id: $pid}) "
                "MERGE (p)-[:PARENT_OF]->(c)",
                cid=child_id,
                pid=parent_id,
            )

    # New: cross-domain links between entities (Solution/Solution, Solution/Task, Task/Task)
    def link_cross_domain(self, left_label: str, left_id: str, rel: str, right_label: str, right_id: str, attrs: Optional[Dict[str, Any]] = None):
        """Create a typed relationship between entities across domains.
        Example: link_cross_domain('Solution','s1','INFLUENCES','Solution','s2', {'weight':0.7})
        """
        if left_label not in ("Solution", "Task") or right_label not in ("Solution", "Task"):
            raise ValueError("left_label/right_label must be 'Solution' or 'Task'")
        attrs = attrs or {}
        set_clause = ", ".join([f"r.{k} = ${k}" for k in attrs.keys()])
        if set_clause:
            set_clause = " SET " + set_clause
        with self.driver.session() as session:
            session.run(
                f"MATCH (a:{left_label} {{id: $left_id}}), (b:{right_label} {{id: $right_id}}) "
                f"MERGE (a)-[r:{rel}]->(b)" + set_clause,
                left_id=left_id,
                right_id=right_id,
                **attrs,
            )

    # Queries with domain support
    def get_lineage(self, solution_id: str, max_depth: int = 5) -> List[Dict[str, Any]]:
        """Get ancestors up to max_depth with their domains."""
        with self.driver.session() as session:
            try:
                query = (
                    "MATCH (s:Solution {id: $solution_id})<-[:PARENT_OF*1..$max_depth]-(ancestor:Solution) "
                    "RETURN ancestor"
                )
                result = session.run(query, solution_id=solution_id, max_depth=max_depth)
                return [dict(record["ancestor"]) for record in result]
            except Exception as e:
                logger.error(f"Failed to get lineage for {solution_id}: {e}")
                return []

    def get_best_solutions(self, task_type: Optional[str] = None, domain: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get best solutions by fitness, optionally filtered by task_type and domain."""
        with self.driver.session() as session:
            try:
                if task_type and domain:
                    query = (
                        "MATCH (s:Solution {task_type: $task_type, domain: $domain}) "
                        "RETURN s ORDER BY s.fitness DESC LIMIT $limit"
                    )
                    result = session.run(query, task_type=task_type, domain=domain, limit=limit)
                elif task_type:
                    query = "MATCH (s:Solution {task_type: $task_type}) RETURN s ORDER BY s.fitness DESC LIMIT $limit"
                    result = session.run(query, task_type=task_type, limit=limit)
                elif domain:
                    query = "MATCH (s:Solution {domain: $domain}) RETURN s ORDER BY s.fitness DESC LIMIT $limit"
                    result = session.run(query, domain=domain, limit=limit)
                else:
                    query = "MATCH (s:Solution) RETURN s ORDER BY s.fitness DESC LIMIT $limit"
                    result = session.run(query, limit=limit)
                return [dict(record["s"]) for record in result]
            except Exception as e:
                logger.error(f"Failed to get best solutions: {e}")
                return []

    def get_pool_statistics(self, pool: str, domain: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for a specific pool, optionally filtered by domain."""
        with self.driver.session() as session:
            try:
                if domain:
                    query = (
                        "MATCH (s:Solution {pool: $pool, domain: $domain}) "
                        "RETURN count(s) as solution_count, avg(s.fitness) as avg_fitness, max(s.fitness) as max_fitness, "
                        "min(s.fitness) as min_fitness, avg(s.token_cost) as avg_token_cost, max(s.generation) as max_generation"
                    )
                    result = session.run(query, pool=pool, domain=domain)
                else:
                    query = (
                        "MATCH (s:Solution {pool: $pool}) "
                        "RETURN count(s) as solution_count, avg(s.fitness) as avg_fitness, max(s.fitness) as max_fitness, "
                        "min(s.fitness) as min_fitness, avg(s.token_cost) as avg_token_cost, max(s.generation) as max_generation"
                    )
                    result = session.run(query, pool=pool)
                record = result.single()
                if record:
                    return dict(record)
                return {}
            except Exception as e:
                logger.error(f"Failed to get pool statistics for {pool}: {e}")
                return {}

    # Migration utility: assign a domain to existing Solution/Task nodes missing the property
    def migrate_assign_default_domain(self, default_domain: str = DEFAULT_DOMAIN) -> Tuple[int, int]:
        """Set domain on existing nodes if missing. Returns (solutions_updated, tasks_updated)."""
        with self.driver.session() as session:
            res1 = session.run(
                "MATCH (s:Solution) WHERE s.domain IS NULL SET s.domain = $d RETURN count(s) as c",
                d=default_domain,
            ).single()
            res2 = session.run(
                "MATCH (t:Task) WHERE t.domain IS NULL SET t.domain = $d RETURN count(t) as c",
                d=default_domain,
            ).single()
            return (res1["c"] if res1 else 0, res2["c"] if res2 else 0)

    def close(self):
        if self.driver:
            self.driver.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
