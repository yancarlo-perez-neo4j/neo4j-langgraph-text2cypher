import pytest
from unittest.mock import Mock, patch
from simple_text2cypher.workflows.simple_text2cypher_workflow import create_simple_text2cypher_workflow
from simple_text2cypher.retrievers.cypher_examples.yaml import YAMLCypherExampleRetriever


def test_workflow_creation(mock_llm, mock_graph, tmp_path):
    """Test that the workflow can be created successfully."""
    # Create a temporary queries file
    queries_file = tmp_path / "test_queries.yml"
    queries_file.write_text("""
questions:
  - question: "Test question"
    cypher: "MATCH (n) RETURN n LIMIT 1"
""")
    
    retriever = YAMLCypherExampleRetriever(str(queries_file))
    
    # Create the workflow
    workflow = create_simple_text2cypher_workflow(
        llm=mock_llm,
        graph=mock_graph,
        cypher_example_retriever=retriever,
        scope_description="Test scope"
    )
    
    # Verify workflow is created
    assert workflow is not None
    
    # Verify nodes are present
    node_names = list(workflow.get_graph().nodes.keys())
    expected_nodes = [
        "guardrails", "planner", "text2cypher", "gather_cypher", 
        "summarize", "validate_final_answer", "final_answer"
    ]
    
    for node in expected_nodes:
        assert node in node_names


def test_workflow_with_custom_parameters(mock_llm, mock_graph, tmp_path):
    """Test workflow creation with custom parameters."""
    queries_file = tmp_path / "test_queries.yml"
    queries_file.write_text("""
questions:
  - question: "Test question"
    cypher: "MATCH (n) RETURN n LIMIT 1"
""")
    
    retriever = YAMLCypherExampleRetriever(str(queries_file))
    
    # Test with custom parameters
    workflow = create_simple_text2cypher_workflow(
        llm=mock_llm,
        graph=mock_graph,
        cypher_example_retriever=retriever,
        scope_description="Custom scope",
        llm_cypher_validation=True,
        max_attempts=5,
        attempt_cypher_execution_on_final_attempt=False
    )
    
    assert workflow is not None