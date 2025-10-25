import pytest
from neo4j import GraphDatabase
from src.utils.neo4j_client import Neo4jClient
from src.models.task import Task
from src.models.solution import Solution


@pytest.fixture
def neo4j_test_client():
    """Create a test Neo4j connection."""
    client = Neo4jClient(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="password"
    )
    yield client
    client.close()


@pytest.fixture
def cleanup_test_db(neo4j_test_client):
    """Remove all test nodes after tests."""
    yield
    with neo4j_test_client.driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")


@pytest.fixture
def test_task():
    """Create a sample Task object."""
    return Task(
        task_id="test_task_1",
        description="Test task description",
        difficulty="medium",
        category="algorithms"
    )


@pytest.fixture
def test_solution():
    """Create a sample Solution object."""
    return Solution(
        solution_id="test_solution_1",
        task_id="test_task_1",
        code="def test(): return True",
        score=85.5,
        generation=1
    )
