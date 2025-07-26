"""
This code is based on content found in the LangGraph documentation: https://python.langchain.com/docs/tutorials/graph/#advanced-implementation-with-langgraph
"""

from typing import Any, Callable, Coroutine, Dict, List

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser

from neo4j_text2cypher.components.state import OverallState
from neo4j_text2cypher.components.summarize.prompts import (
    create_summarization_prompt_template,
)

generate_summary_prompt = create_summarization_prompt_template()


def format_conversation_history_for_summary(history: List[Dict[str, Any]]) -> str:
    """
    Format conversation history for the summarization prompt.

    Parameters
    ----------
    history : List[Dict[str, Any]]
        The conversation history.

    Returns
    -------
    str
        Formatted conversation history string.
    """
    if not history:
        return "No previous conversation history."

    formatted_history = "Previous conversation context:\n"
    for i, record in enumerate(history, 1):
        formatted_history += f"{i}. Previous question: {record['question']}\n"
        formatted_history += f"   Previous answer: {record['answer']}\n"

    return formatted_history


def create_summarization_node(
    llm: BaseChatModel,
) -> Callable[[OverallState], Coroutine[Any, Any, dict[str, Any]]]:
    """
    Create a Summarization node for a LangGraph workflow.

    Parameters
    ----------
    llm : BaseChatModel
        The LLM do perform processing.

    Returns
    -------
    Callable[[OverallState], OutputState]
        The LangGraph node.
    """

    generate_summary = generate_summary_prompt | llm | StrOutputParser()

    async def summarize(state: OverallState) -> Dict[str, Any]:
        """
        Summarize results of the performed Cypher queries.
        """

        # Separate visualization and non-visualization queries
        all_cyphers = state.get("cyphers", list())
        viz_cyphers = [c for c in all_cyphers if c.get("visualization_requested", False)]
        regular_cyphers = [c for c in all_cyphers if not c.get("visualization_requested", False)]
        
        # Get results only from non-visualization queries for summarization
        results_to_summarize = [
            cypher.get("records")
            for cypher in regular_cyphers
            if cypher.get("records") is not None
        ]

        if results_to_summarize:
            # Summarize non-visualization results
            history = state.get("history", [])
            conversation_history = format_conversation_history_for_summary(history)

            summary = await generate_summary.ainvoke(
                {
                    "question": state.get("question"),
                    "results": results_to_summarize,
                    "conversation_history": conversation_history,
                }
            )
            
            # Add note about visualizations if present
            if viz_cyphers:
                viz_count = len(viz_cyphers)
                viz_note = f"\n\n{viz_count} graph visualization{'s' if viz_count > 1 else ''} available in below details."
                summary += viz_note

        elif viz_cyphers:
            # Only visualization queries - use generic message
            summary = "Graph visualization is available below showing the requested data relationships."
        else:
            summary = "No data to summarize."

        return {"summary": summary, "steps": ["summarize"]}

    return summarize
