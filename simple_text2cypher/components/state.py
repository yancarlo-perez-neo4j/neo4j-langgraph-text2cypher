from operator import add
from typing import Annotated, Any, Dict, List, Optional

from langchain_core.messages import ToolCall
from typing_extensions import TypedDict

from .models import Task
from .text2cypher.state import CypherOutputState


class CypherHistoryRecord(TypedDict):
    """A simplified representation of the CypherOutputState"""

    task: str
    statement: str
    records: List[Dict[str, Any]]


class HistoryRecord(TypedDict):
    """Information that may be relevant to future user questions."""

    question: str
    answer: str
    cyphers: List[CypherHistoryRecord]


def update_history(
    history: List[HistoryRecord], new: List[HistoryRecord]
) -> List[HistoryRecord]:
    """
    Update the history record. Allow only a max number of records to be stored at any time.

    Parameters
    ----------
    history : List[HistoryRecord]
        The current history list.
    new : List[HistoryRecord]
        The new record to add. Should be a single entry list.

    Returns
    -------
    List[HistoryRecord]
        A new List with the record added and old records removed to maintain size.
    """

    SIZE: int = 5

    history.extend(new)
    return history[-SIZE:]


class InputState(TypedDict):
    """The input state for multi agent workflows."""

    question: str
    data: List[Dict[str, Any]]
    history: Annotated[List[HistoryRecord], update_history]


class OverallState(TypedDict):
    """The main state in text2cypher workflows."""

    question: str
    tasks: Annotated[List[Task], add]
    next_action: str
    cyphers: Annotated[List[CypherOutputState], add]
    summary: str
    steps: Annotated[List[Any], add]
    history: Annotated[List[HistoryRecord], update_history]


class OutputState(TypedDict):
    """The final output for text2cypher workflows."""

    answer: str
    question: str
    steps: List[Any]
    cyphers: List[CypherOutputState]
    history: Annotated[List[HistoryRecord], update_history]


class TaskState(TypedDict):
    """The state of a task."""

    question: str
    parent_task: str
    data: CypherOutputState


class PredefinedCypherInputState(TypedDict):
    """The input state for a predefined Cypher node."""

    task: str
    query_name: str
    query_parameters: Dict[str, Any]
    prev_steps: List[Any]


class ToolSelectionInputState(TypedDict):
    """The input state for the Tool Selection node."""

    question: str
    parent_task: str
    context: Any


class ToolSelectionOutputState(TypedDict):
    tool_selection_task: str
    tool_call: Optional[ToolCall]
    prev_steps: Optional[List[Any]]


class ToolSelectionErrorState(TypedDict):
    """The input state to the tool selection error handling node."""

    task: str
    errors: List[str]
    cypher_steps: List[Any]
