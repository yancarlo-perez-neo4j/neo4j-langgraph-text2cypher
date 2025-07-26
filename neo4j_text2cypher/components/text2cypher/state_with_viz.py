"""
Extended state classes that include visualization support.
"""

from typing import Any, Optional

from neo4j_text2cypher.components.text2cypher.state import (
    CypherState,
    CypherOutputState
)


class CypherStateWithViz(CypherState):
    """Extended CypherState that includes visualization flag."""
    visualization_requested: bool = False


class CypherOutputStateWithViz(CypherOutputState):
    """Extended CypherOutputState that can include graph result."""
    visualization_requested: bool = False
    graph_result: Optional[Any] = None  # Will hold neo4j.Result.graph when available