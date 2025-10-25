import pytest
from src.utils import Neo4jLineageTracker, Solution, Task


def test_connection(neo4j_test_client):
    """Test that Neo4j connection can be established."""
    assert neo4j_test_client is not None
    # Verify connection by running a simple query
    with neo4j_test_client.session() as session:
        result = session.run("RETURN 1 as num")
        assert result.single()["num"] == 1


def test_add_solution(neo4j_test_client, cleanup_test_db):
    """Test adding a solution to Neo4j and verifying it exists."""
    tracker = Neo4jLineageTracker(neo4j_test_client)
    
    # Create a task and solution
    task = Task(
        task_id="test_task_1",
        description="Test task",
        dataset_name="test_dataset"
    )
    solution = Solution(
        solution_id="sol_1",
        code="print('hello')",
        fitness=0.85,
        task=task
    )
    
    # Add solution to Neo4j
    tracker.add_solution(solution)
    
    # Verify the solution node exists with correct properties
    with neo4j_test_client.session() as session:
        result = session.run(
            "MATCH (s:Solution {solution_id: $sid}) RETURN s",
            sid=solution.solution_id
        )
        node = result.single()["s"]
        assert node["solution_id"] == "sol_1"
        assert node["fitness"] == 0.85
        assert node["task_id"] == "test_task_1"


def test_evolutionary_relationship(neo4j_test_client, cleanup_test_db):
    """Test creating EVOLVED_FROM relationship between parent and child solutions."""
    tracker = Neo4jLineageTracker(neo4j_test_client)
    
    # Create parent solution
    task = Task(
        task_id="test_task_2",
        description="Test task",
        dataset_name="test_dataset"
    )
    parent_solution = Solution(
        solution_id="parent_1",
        code="print('parent')",
        fitness=0.75,
        task=task
    )
    
    # Create child solution with parent_ids
    child_solution = Solution(
        solution_id="child_1",
        code="print('child')",
        fitness=0.85,
        task=task,
        parent_ids=["parent_1"]
    )
    
    # Add both solutions
    tracker.add_solution(parent_solution)
    tracker.add_solution(child_solution)
    
    # Verify EVOLVED_FROM relationship exists
    with neo4j_test_client.session() as session:
        result = session.run(
            """MATCH (child:Solution {solution_id: $child_id})
                      -[r:EVOLVED_FROM]->
                      (parent:Solution {solution_id: $parent_id})
               RETURN r""",
            child_id="child_1",
            parent_id="parent_1"
        )
        relationship = result.single()
        assert relationship is not None


def test_hybrid_relationship(neo4j_test_client, cleanup_test_db):
    """Test creating HYBRID_OF relationships with two parent solutions."""
    tracker = Neo4jLineageTracker(neo4j_test_client)
    
    # Create two parent solutions
    task = Task(
        task_id="test_task_3",
        description="Test task",
        dataset_name="test_dataset"
    )
    parent1 = Solution(
        solution_id="parent_a",
        code="print('parent_a')",
        fitness=0.70,
        task=task
    )
    parent2 = Solution(
        solution_id="parent_b",
        code="print('parent_b')",
        fitness=0.75,
        task=task
    )
    
    # Create hybrid child with both parent IDs
    hybrid_child = Solution(
        solution_id="hybrid_1",
        code="print('hybrid')",
        fitness=0.90,
        task=task,
        parent_ids=["parent_a", "parent_b"]
    )
    
    # Add all solutions
    tracker.add_solution(parent1)
    tracker.add_solution(parent2)
    tracker.add_solution(hybrid_child)
    
    # Verify HYBRID_OF relationships exist
    with neo4j_test_client.session() as session:
        result = session.run(
            """MATCH (child:Solution {solution_id: $child_id})
                      -[r:HYBRID_OF]->
                      (parent:Solution)
               RETURN count(r) as rel_count""",
            child_id="hybrid_1"
        )
        count = result.single()["rel_count"]
        assert count == 2


def test_query_best_fitness(neo4j_test_client, cleanup_test_db):
    """Test querying for maximum fitness score."""
    tracker = Neo4jLineageTracker(neo4j_test_client)
    
    # Add multiple solutions with different fitness scores
    task = Task(
        task_id="test_task_4",
        description="Test task",
        dataset_name="test_dataset"
    )
    
    fitness_scores = [0.65, 0.92, 0.78, 0.85, 0.70]
    for i, fitness in enumerate(fitness_scores):
        solution = Solution(
            solution_id=f"sol_{i}",
            code=f"print('solution {i}')",
            fitness=fitness,
            task=task
        )
        tracker.add_solution(solution)
    
    # Query for MAX fitness
    with neo4j_test_client.session() as session:
        result = session.run(
            "MATCH (s:Solution) RETURN MAX(s.fitness) as max_fitness"
        )
        max_fitness = result.single()["max_fitness"]
        assert max_fitness == 0.92
