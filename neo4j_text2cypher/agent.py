"""This file is for LangGraph Studio testing."""

import os
from langchain_neo4j import Neo4jGraph
from langchain_openai import ChatOpenAI

from neo4j_text2cypher.retrievers.cypher_examples import YAMLCypherExampleRetriever
from neo4j_text2cypher.workflows.neo4j_text2cypher_workflow import create_neo4j_text2cypher_workflow

# Initialize components
neo4j_graph = Neo4jGraph(enhanced_schema=True)
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Use example queries file
cypher_query_yaml_file_path = "data/example/queries.yml"
cypher_example_retriever = YAMLCypherExampleRetriever(
    cypher_query_yaml_file_path=cypher_query_yaml_file_path
)

# Create the graph to be found by LangGraph Studio
graph = create_neo4j_text2cypher_workflow(
    llm=llm,
    graph=neo4j_graph,
    cypher_example_retriever=cypher_example_retriever,
    scope_description="This application answers questions about your Neo4j graph database.",
    llm_cypher_validation=False,
    attempt_cypher_execution_on_final_attempt=True,
)