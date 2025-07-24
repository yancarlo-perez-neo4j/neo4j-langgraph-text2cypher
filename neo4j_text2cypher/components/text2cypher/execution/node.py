"""
This code is based on content found in the LangGraph documentation: https://python.langchain.com/docs/tutorials/graph/#advanced-implementation-with-langgraph
"""

from typing import Any, Callable, Coroutine, Dict, List

from langchain_neo4j import Neo4jGraph

from neo4j_text2cypher.components.text2cypher.state import (
    CypherOutputState,
    CypherState,
)
from neo4j_text2cypher.constants import NO_CYPHER_RESULTS


def create_text2cypher_execution_node(
    graph: Neo4jGraph,
) -> Callable[
    [CypherState], Coroutine[Any, Any, Dict[str, List[CypherOutputState] | List[str]]]
]:
    """
    Create a Text2Cypher execution node for a LangGraph workflow.

    Parameters
    ----------
    graph : Neo4jGraph
        The Neo4j graph wrapper.

    Returns
    -------
    Callable[[CypherState], Dict[str, List[CypherOutputState] | List[str]]]
        The LangGraph node.
    """

    async def execute_cypher(
        state: CypherState,
    ) -> Dict[str, List[CypherOutputState] | List[Any]]:
        """
        Executes the given Cypher statement.
        """
        records = graph.query(state.get("statement", ""))
        steps = state.get("cypher_steps", list())
        steps.append("execute_cypher")
        return {
            "cyphers": [
                CypherOutputState(
                    **{
                        "task": state.get("task", ""),
                        "statement": state.get("statement", ""),
                        "parameters": None,
                        "errors": state.get("errors", list()),
                        "records": records if records else NO_CYPHER_RESULTS,
                        "cypher_steps": steps,
                    }
                )
            ],
            "steps": [steps],
        }

    return execute_cypher
