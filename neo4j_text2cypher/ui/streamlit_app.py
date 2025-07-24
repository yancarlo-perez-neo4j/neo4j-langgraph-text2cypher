import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from dotenv import load_dotenv
from langchain_neo4j import Neo4jGraph
from langchain_openai import ChatOpenAI

from neo4j_text2cypher.retrievers import ConfigCypherExampleRetriever
from neo4j_text2cypher.ui.components import chat, display_chat_history, sidebar
from neo4j_text2cypher.utils.config import ConfigLoader
from neo4j_text2cypher.utils.debug import setup_debug_logging
from neo4j_text2cypher.workflows.neo4j_text2cypher_workflow import (
    create_neo4j_text2cypher_workflow,
)

if load_dotenv():
    print("Env Loaded Successfully!")
else:
    print("Unable to Load Environment.")


def get_config_loader() -> ConfigLoader:
    """Parse the command line arguments and return config loader."""

    args = sys.argv
    if len(args) > 1:
        config_path: str = args[1]

        # Only support YAML configs
        if config_path.lower().endswith((".yml", ".yaml")):
            return ConfigLoader(config_path)
        else:
            raise ValueError(
                f"Only YAML config files (.yml/.yaml) are supported: {config_path}"
            )
    else:
        raise ValueError(
            "Config file path is required. Usage: streamlit run app.py <config.yml>"
        )


def initialize_state(config_loader: ConfigLoader) -> None:
    """Initialize the application state."""

    if "agent" not in st.session_state:
        # Setup debug logging from config
        debug_config = config_loader.get_debug_config()
        setup_debug_logging(debug_config)

        # Initialize Neo4j connection with app-specific settings
        neo4j_params = config_loader.get_neo4j_connection_params()
        graph = Neo4jGraph(**neo4j_params)

        # Initialize LLM
        llm = ChatOpenAI(model="gpt-4o", temperature=0)

        # Use unified config retriever
        cypher_example_retriever = ConfigCypherExampleRetriever(
            config_path=str(config_loader.config_path)
        )

        # Get config for UI
        streamlit_config = config_loader.get_streamlit_config()

        # Create the workflow
        agent = create_neo4j_text2cypher_workflow(
            llm=llm,
            graph=graph,
            scope_description=streamlit_config.scope_description,
            cypher_example_retriever=cypher_example_retriever,
            attempt_cypher_execution_on_final_attempt=False,
        )

        st.session_state.agent = agent
        st.session_state.messages = []
        st.session_state.example_questions = streamlit_config.example_questions


async def run_app(
    title: str = "Simple Text2Cypher Assistant", scope_description: str = ""
) -> None:
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

    config_loader = get_config_loader()
    streamlit_config = config_loader.get_streamlit_config()

    st.set_page_config(page_title=streamlit_config.title, page_icon="🤖", layout="wide")

    initialize_state(config_loader)

    asyncio.run(
        run_app(
            title=streamlit_config.title,
            scope_description=streamlit_config.scope_description,
        )
    )


if __name__ == "__main__":
    main()
