from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_neo4j import Neo4jGraph
from langgraph.constants import END, START
from langgraph.graph.state import CompiledStateGraph, StateGraph

from neo4j_text2cypher.components.final_answer import create_final_answer_node
from neo4j_text2cypher.components.guardrails import create_guardrails_node
from neo4j_text2cypher.components.planner import create_planner_node
from neo4j_text2cypher.components.state import (
    InputState,
    OutputState,
    OverallState,
)
from neo4j_text2cypher.components.summarize import create_summarization_node
from neo4j_text2cypher.retrievers import ConfigCypherExampleRetriever
from neo4j_text2cypher.workflows.edges import (
    guardrails_conditional_edge,
    query_mapper_edge,
)
from neo4j_text2cypher.workflows.single_agent import create_text2cypher_agent


def create_neo4j_text2cypher_workflow(
    llm: BaseChatModel,
    graph: Neo4jGraph,
    cypher_example_retriever: ConfigCypherExampleRetriever,
    scope_description: Optional[str] = None,
    max_attempts: int = 3,
    attempt_cypher_execution_on_final_attempt: bool = False,
) -> CompiledStateGraph:
    """
    Create a simplified Text2Cypher workflow using LangGraph.
    This workflow includes guardrails, query parsing, text2cypher processing and summarization.

    Parameters
    ----------
    llm : BaseChatModel
        The LLM to use for processing
    graph : Neo4jGraph
        The Neo4j graph wrapper.
    scope_description: Optional[str], optional
        A short description of the application scope, by default None
    cypher_example_retriever: ConfigCypherExampleRetriever
        The retriever used to collect Cypher examples for few shot prompting.
    max_attempts: int, optional
        The max number of allowed attempts to generate valid Cypher, by default 3
    attempt_cypher_execution_on_final_attempt, bool, optional
        THIS MAY BE DANGEROUS.
        Whether to attempt Cypher execution on the last attempt, regardless of if the Cypher contains errors, by default False

    Returns
    -------
    CompiledStateGraph
        The workflow.
    """

    guardrails = create_guardrails_node(
        llm=llm, graph=graph, scope_description=scope_description
    )
    planner = create_planner_node(llm=llm)
    text2cypher = create_text2cypher_agent(
        llm=llm,
        graph=graph,
        cypher_example_retriever=cypher_example_retriever,
        max_attempts=max_attempts,
        attempt_cypher_execution_on_final_attempt=attempt_cypher_execution_on_final_attempt,
    )
    summarize = create_summarization_node(llm=llm)
    final_answer = create_final_answer_node()


    main_graph_builder = StateGraph(OverallState, input=InputState, output=OutputState)

    main_graph_builder.add_node(guardrails)
    main_graph_builder.add_node(planner)
    main_graph_builder.add_node("text2cypher", text2cypher)
    main_graph_builder.add_node(summarize)
    main_graph_builder.add_node(final_answer)


    main_graph_builder.add_edge(START, "guardrails")
    main_graph_builder.add_conditional_edges(
        "guardrails",
        guardrails_conditional_edge,
    )
    main_graph_builder.add_conditional_edges(
        "planner",
        query_mapper_edge,  # type: ignore[arg-type, unused-ignore]
        ["text2cypher"],
    )
    main_graph_builder.add_edge("text2cypher", "summarize")

    main_graph_builder.add_edge("summarize", "final_answer")

    main_graph_builder.add_edge("final_answer", END)

    return main_graph_builder.compile()
