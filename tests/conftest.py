import pytest
from unittest.mock import Mock
from langchain_neo4j import Neo4jGraph
from langchain_openai import ChatOpenAI

@pytest.fixture
def mock_llm():
    """Mock LLM for testing."""
    return Mock(spec=ChatOpenAI)

@pytest.fixture
def mock_graph():
    """Mock Neo4j graph for testing."""
    mock = Mock(spec=Neo4jGraph)
    mock.schema = "Mock graph schema"
    return mock

@pytest.fixture
def sample_queries_yaml():
    """Sample queries YAML content for testing."""
    return """
questions:
  - question: "How many nodes?"
    cypher: "MATCH (n) RETURN count(n)"
  - question: "Show labels"
    cypher: "CALL db.labels()"
"""