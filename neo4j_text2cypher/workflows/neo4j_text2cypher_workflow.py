from typing import Optional, Dict, Any

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
from neo4j_text2cypher.components.validate_final_answer import create_validate_final_answer_node
from neo4j_text2cypher.retrievers.cypher_examples.base import BaseCypherExampleRetriever
from neo4j_text2cypher.workflows.single_agent import create_text2cypher_agent
from neo4j_text2cypher.workflows.edges import (
    guardrails_conditional_edge,
    query_mapper_edge,
    validate_final_answer_router,
)


def create_neo4j_text2cypher_workflow(
    llm: BaseChatModel,
    graph: Neo4jGraph,
    cypher_example_retriever: BaseCypherExampleRetriever,
    scope_description: Optional[str] = None,
    llm_cypher_validation: bool = True,
    max_attempts: int = 3,
    attempt_cypher_execution_on_final_attempt: bool = False,
    enable_final_answer_validation: bool = False,
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
    cypher_example_retriever: BaseCypherExampleRetriever
        The retriever used to collect Cypher examples for few shot prompting.
    llm_cypher_validation : bool, optional
        Whether to perform LLM validation with the provided LLM, by default True
    max_attempts: int, optional
        The max number of allowed attempts to generate valid Cypher, by default 3
    attempt_cypher_execution_on_final_attempt, bool, optional
        THIS MAY BE DANGEROUS.
        Whether to attempt Cypher execution on the last attempt, regardless of if the Cypher contains errors, by default False
    enable_final_answer_validation : bool, optional
        Whether to enable final answer validation step that can loop back for corrections, by default False

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
        llm_cypher_validation=llm_cypher_validation,
        max_attempts=max_attempts,
        attempt_cypher_execution_on_final_attempt=attempt_cypher_execution_on_final_attempt,
    )
    summarize = create_summarization_node(llm=llm)
    final_answer = create_final_answer_node()
    
    # Conditionally create validation node
    if enable_final_answer_validation:
        validate_final_answer = create_validate_final_answer_node(
            llm=llm, graph=graph, loop_back_node="text2cypher", max_validation_attempts=2
        )

    main_graph_builder = StateGraph(OverallState, input=InputState, output=OutputState)

    main_graph_builder.add_node(guardrails)
    main_graph_builder.add_node(planner)
    main_graph_builder.add_node("text2cypher", text2cypher)
    main_graph_builder.add_node(summarize)
    main_graph_builder.add_node(final_answer)
    
    # Conditionally add validation node
    if enable_final_answer_validation:
        main_graph_builder.add_node(validate_final_answer)

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
    
    # Conditionally add validation edges
    if enable_final_answer_validation:
        main_graph_builder.add_edge("summarize", "validate_final_answer")
        main_graph_builder.add_conditional_edges(
            "validate_final_answer",
            validate_final_answer_router,
            ["text2cypher", "final_answer"],
        )
    else:
        main_graph_builder.add_edge("summarize", "final_answer")
    
    main_graph_builder.add_edge("final_answer", END)

    return main_graph_builder.compile()