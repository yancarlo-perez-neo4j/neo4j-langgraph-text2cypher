import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from dotenv import load_dotenv
from langchain_neo4j import Neo4jGraph
from langchain_openai import ChatOpenAI

from neo4j_text2cypher.retrievers.cypher_examples import YAMLCypherExampleRetriever
from neo4j_text2cypher.ui.components import chat, display_chat_history, sidebar
from neo4j_text2cypher.workflows.neo4j_text2cypher_workflow import create_neo4j_text2cypher_workflow

if load_dotenv():
    print("Env Loaded Successfully!")
else:
    print("Unable to Load Environment.")


def get_args() -> Dict[str, Any]:
    """Parse the command line arguments to configure the application."""

    args = sys.argv
    if len(args) > 1:
        config_path: str = args[1]
        assert config_path.lower().endswith(
            ".json"
        ), f"provided file is not JSON | {config_path}"
        with open(config_path, "r") as f:
            config: Dict[str, Any] = json.load(f)
    else:
        config = dict()

    return config


def initialize_state(
    cypher_query_yaml_file_path: str,
    scope_description: str,
    example_questions: List[str] = list(),
) -> None:
    """
    Initialize the application state.
    """

    if "agent" not in st.session_state:
        # Initialize graph and LLM
        graph = Neo4jGraph(enhanced_schema=True)
        llm = ChatOpenAI(model="gpt-4o", temperature=0)

        # Initialize cypher example retriever
        cypher_example_retriever = YAMLCypherExampleRetriever(
            cypher_query_yaml_file_path=cypher_query_yaml_file_path
        )

        # Create the workflow
        agent = create_neo4j_text2cypher_workflow(
            llm=llm,
            graph=graph,
            scope_description=scope_description,
            cypher_example_retriever=cypher_example_retriever,
            llm_cypher_validation=False,
            attempt_cypher_execution_on_final_attempt=True,
        )

        st.session_state.agent = agent
        st.session_state.messages = []
        st.session_state.example_questions = example_questions


async def run_app(title: str = "Simple Text2Cypher Assistant", scope_description: str = "") -> None:
    """
    Run the Streamlit application.
    """

    st.title(title)
    if scope_description:
        st.write(scope_description)
    sidebar()
    display_chat_history()
    
    # Prompt for user input and save and display
    if question := st.chat_input("Ask a question about your graph data..."):
        st.session_state["current_question"] = question

    if "current_question" in st.session_state:
        await chat(str(st.session_state.get("current_question", "")))


def main() -> None:
    """
    Main function to run the Streamlit application.
    """

    config = get_args()

    title = config.get("title", "Simple Text2Cypher Assistant")
    scope_description = config.get(
        "scope_description", "This application answers questions using a Neo4j graph database."
    )
    cypher_query_yaml_file_path = config.get(
        "cypher_query_yaml_file_path", "data/example/queries.yml"
    )
    example_questions = config.get("example_questions", [])

    st.set_page_config(page_title=title, page_icon="🤖", layout="wide")

    initialize_state(
        cypher_query_yaml_file_path=cypher_query_yaml_file_path,
        scope_description=scope_description,
        example_questions=example_questions,
    )

    asyncio.run(run_app(title=title, scope_description=scope_description))


if __name__ == "__main__":
    main()