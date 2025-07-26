"""
This file contains classes that manage the state of a Text2Cypher Agent or subgraph.
"""

from operator import add
from typing import Annotated, Any, Dict, List, Optional

from typing_extensions import TypedDict


class CypherInputState(TypedDict):
    task: str
    prev_steps: List[str]


class CypherState(TypedDict):
    task: str
    statement: str
    parameters: Optional[Dict[str, Any]]
    errors: List[str]
    records: List[Dict[str, Any]]
    next_action_cypher: str
    attempts: int
    cypher_steps: Annotated[List[str], add]
    visualization_requested: bool


class CypherOutputState(TypedDict):
    task: str
    statement: str
    parameters: Optional[Dict[str, Any]]
    errors: List[str]
    records: List[Dict[str, Any]]
    cypher_steps: List[str]
    visualization_requested: bool
