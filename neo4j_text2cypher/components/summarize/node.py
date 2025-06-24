"""
This code is based on content found in the LangGraph documentation: https://python.langchain.com/docs/tutorials/graph/#advanced-implementation-with-langgraph
"""

from typing import Any, Callable, Coroutine, Dict

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser

from neo4j_text2cypher.components.state import OverallState
from neo4j_text2cypher.components.summarize.prompts import create_summarization_prompt_template

generate_summary_prompt = create_summarization_prompt_template()


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

        results = [
            cypher.get("records")
            for cypher in state.get("cyphers", list())
            if cypher.get("records") is not None
        ]

        if results:
            summary = await generate_summary.ainvoke(
                {
                    "question": state.get("question"),
                    "results": results,
                }
            )

        else:
            summary = "No data to summarize."

        return {"summary": summary, "steps": ["summarize"]}

    return summarize
