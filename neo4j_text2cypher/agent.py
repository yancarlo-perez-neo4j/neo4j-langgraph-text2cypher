"""This file is for LangGraph Studio testing."""

import os
from langchain_neo4j import Neo4jGraph
from langchain_openai import ChatOpenAI

from neo4j_text2cypher.retrievers.cypher_examples import UnifiedConfigCypherExampleRetriever
from neo4j_text2cypher.utils.config import UnifiedAppConfigLoader
from neo4j_text2cypher.utils.debug import setup_debug_logging
from neo4j_text2cypher.workflows.neo4j_text2cypher_workflow import create_neo4j_text2cypher_workflow

# Use unified configuration
config_path = "example_apps/iqs_data_explorer/app-config.yml"
config_loader = UnifiedAppConfigLoader(config_path)

# Setup debug logging from config
debug_config = config_loader.get_debug_config()
setup_debug_logging(debug_config)

# Initialize Neo4j connection with app-specific settings
neo4j_params = config_loader.get_neo4j_connection_params()
neo4j_graph = Neo4jGraph(**neo4j_params)

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Use unified config retriever
cypher_example_retriever = UnifiedConfigCypherExampleRetriever(
    config_path=config_path
)

# Get scope description from config
streamlit_config = config_loader.get_streamlit_config()

# Create the graph to be found by LangGraph Studio
graph = create_neo4j_text2cypher_workflow(
    llm=llm,
    graph=neo4j_graph,
    cypher_example_retriever=cypher_example_retriever,
    scope_description=streamlit_config.scope_description,
    llm_cypher_validation=False,
    attempt_cypher_execution_on_final_attempt=True,
)