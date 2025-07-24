from typing import Any, Callable, Coroutine, Dict, List

from langchain_core.language_models import BaseChatModel
from langchain_core.runnables.base import Runnable

from neo4j_text2cypher.components.models import Task
from neo4j_text2cypher.components.planner.models import PlannerOutput
from neo4j_text2cypher.components.planner.prompts import create_planner_prompt_template
from neo4j_text2cypher.components.state import InputState
from neo4j_text2cypher.utils.debug import get_planner_logger

planner_prompt = create_planner_prompt_template()


def format_conversation_history(history: List[Dict[str, Any]]) -> str:
    """
    Format conversation history for the planner prompt.

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

    formatted_history = "Previous conversation history:\n"
    for i, record in enumerate(history, 1):
        formatted_history += f"\n{i}. Q: {record['question']}\n"
        formatted_history += f"   A: {record['answer']}\n"

    return formatted_history


def create_planner_node(
    llm: BaseChatModel, ignore_node: bool = False
) -> Callable[[InputState], Coroutine[Any, Any, Dict[str, Any]]]:
    """
    Create a planner node to be used in a LangGraph workflow.

    Parameters
    ----------
    llm : BaseChatModel
        The LLM used to process data.
    ignore_node : bool, optional
        Whether to ignore this node in the workflow, by default False

    Returns
    -------
    Callable[[InputState], OverallState]
        The LangGraph node.
    """

    planner_chain: Runnable[Dict[str, Any], Any] = (
        planner_prompt
        | llm.with_structured_output(PlannerOutput, method="function_calling")
    )

    async def planner(state: InputState) -> Dict[str, Any]:
        """
        Break user query into chunks, if appropriate.
        """

        if not ignore_node:
            # Format conversation history for the prompt
            history = state.get("history", [])
            conversation_history = format_conversation_history(history)

            planner_output: PlannerOutput = await planner_chain.ainvoke(
                {
                    "question": state.get("question", ""),
                    "conversation_history": conversation_history,
                }
            )

            # Debug: Print planner output
            logger = get_planner_logger()
            logger.debug(f"🔍 PLANNER DEBUG - Question: {state.get('question', '')}")
            logger.debug(
                f"🔍 PLANNER DEBUG - History provided: {conversation_history[:100]}..."
            )
            logger.debug(
                f"🔍 PLANNER DEBUG - Tasks generated: {len(planner_output.tasks)}"
            )
            for i, task in enumerate(planner_output.tasks):
                logger.debug(f"🔍 PLANNER DEBUG - Task {i+1}: {task.question}")
            logger.debug(
                "🔍 PLANNER DEBUG - Tasks will be routed to text2cypher pipeline"
            )
        else:
            planner_output = PlannerOutput(tasks=[])
        return {
            "tasks": planner_output.tasks
            or [
                Task(
                    question=state.get("question", ""),
                    parent_task=state.get("question", ""),
                )
            ],
            "steps": ["planner"],
        }

    return planner
