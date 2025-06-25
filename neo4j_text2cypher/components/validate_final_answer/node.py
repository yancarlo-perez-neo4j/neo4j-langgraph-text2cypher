from typing import Any, Callable, Coroutine, Dict

from langchain_core.language_models import BaseChatModel
from langchain_core.runnables.base import Runnable
from langchain_neo4j import Neo4jGraph

from neo4j_text2cypher.components.state import OverallState
from neo4j_text2cypher.components.models import Task
from neo4j_text2cypher.components.utils.utils import retrieve_and_parse_schema_from_graph_for_prompts
from .models import ValidateFinalAnswerResponse
from .prompts import create_validate_final_answer_prompt_template


def create_validate_final_answer_node(
    llm: BaseChatModel, graph: Neo4jGraph, loop_back_node: str = "text2cypher", max_validation_attempts: int = 2
) -> Callable[[OverallState], Coroutine[Any, Any, dict[str, Any]]]:
    """
    Create a Validate Final Answer node for a LangGraph workflow.

    Parameters
    ----------
    llm : BaseChatModel
        The LLM do perform processing.
    graph : Neo4jGraph
        The Neo4j graph wrapper.
    loop_back_node : str, optional
            The name of the node or subgraph to return to with follow up questions, by default "text2cypher"
    max_validation_attempts : int, optional
            Maximum number of validation attempts before accepting the answer, by default 2

    Returns
    -------
    Callable[[OverallState], Dict[str, Any]]
        The LangGraph node.
    """

    validate_final_answer_chain: Runnable[Dict[str, Any], Any] = (
        create_validate_final_answer_prompt_template()
        | llm.with_structured_output(ValidateFinalAnswerResponse)
    )

    async def validate_final_answer(state: OverallState) -> Dict[str, Any]:
        """
        Validate that the final answer sufficiently answers the initial question before returning to the user.

        Parameters
        ----------
        state : OverallState
            The current state.
        loop_back_node : str, optional
            The name of the node or subgraph to return to with follow up questions, by default "text2cypher"

        Returns
        -------
        Dict[str, Any]
            Updates to the state.
        """

        # Track validation attempts to prevent infinite loops
        validation_attempts = state.get("validation_attempts", 0) + 1
        
        response: ValidateFinalAnswerResponse = (
            await validate_final_answer_chain.ainvoke(
                {
                    "question": state.get("question"),
                    "answer": state.get("summary"),
                    "schema": retrieve_and_parse_schema_from_graph_for_prompts(graph),
                    "data": [
                        cypher.get("records") for cypher in state.get("cyphers", list())
                    ],
                }
            )
        )

        to_return: Dict[str, Any] = {
            "steps": ["validate_final_answer"],
            "validation_attempts": validation_attempts
        }

        # Accept answer if valid OR if we've reached max attempts
        if response.valid or validation_attempts >= max_validation_attempts:
            to_return.update({"next_action": "final_answer"})
            if validation_attempts >= max_validation_attempts and not response.valid:
                # Add note that validation was skipped due to attempt limit
                current_summary = state.get("summary", "")
                to_return.update({
                    "summary": current_summary + f"\n\n*Note: Answer provided after {max_validation_attempts} validation attempts.*"
                })
        else:
            to_return.update(
                {
                    "next_action": loop_back_node,
                    "subquestions": [
                        Task(
                            question=response.follow_up_question or "",
                            parent_task=f"follow up question (attempt {validation_attempts})",
                        )
                    ],
                }
            )

        return to_return

    return validate_final_answer
