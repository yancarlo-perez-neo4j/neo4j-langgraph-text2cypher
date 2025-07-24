"""
This code is based on content found in the LangGraph documentation: https://python.langchain.com/docs/tutorials/graph/#advanced-implementation-with-langgraph
"""

from typing import Any, Callable, Coroutine, Dict

from langchain_core.language_models import BaseChatModel
from langchain_neo4j import Neo4jGraph

from neo4j_text2cypher.components.text2cypher.state import CypherState
from neo4j_text2cypher.components.text2cypher.validation.models import (
    ValidateCypherOutput,
)
from neo4j_text2cypher.components.text2cypher.validation.prompts import (
    create_text2cypher_validation_prompt_template,
)
from neo4j_text2cypher.components.text2cypher.validation.validators import (
    correct_cypher_query_relationship_direction,
    validate_cypher_query_syntax,
    validate_cypher_query_with_llm,
    validate_no_writes_in_cypher_query,
)
from neo4j_text2cypher.utils.debug import get_validation_logger

validation_prompt_template = create_text2cypher_validation_prompt_template()


def create_text2cypher_validation_node(
    graph: Neo4jGraph,
    llm: BaseChatModel,
    max_attempts: int = 3,
    attempt_cypher_execution_on_final_attempt: bool = False,
) -> Callable[[CypherState], Coroutine[Any, Any, dict[str, Any]]]:
    """
    Create a Text2Cypher query validation node for a LangGraph workflow.
    This is the last node in the workflow before Cypher execution may be attempted.
    If errors are detected and max attempts have not been reached, then the Cypher Statement must be corrected by the Correction node.

    Parameters
    ----------
    graph : Neo4jGraph
        The Neo4j graph wrapper.
    llm : BaseChatModel
        The LLM to use for processing validation
    max_attempts: int, optional
        The max number of allowed attempts to generate valid Cypher, by default 3
    attempt_cypher_execution_on_final_attempt, bool, optional
        THIS MAY BE DANGEROUS.
        Whether to attempt Cypher execution on the last attempt, regardless of if the Cypher contains errors, by default False

    Returns
    -------
    Callable[[CypherState], CypherState]
        The LangGraph node.
    """

    validate_cypher_chain = validation_prompt_template | llm.with_structured_output(
        ValidateCypherOutput, method="function_calling"
    )

    async def validate_cypher(state: CypherState) -> Dict[str, Any]:
        """
        Validates the Cypher statements and maps any property values to the database.
        """

        GENERATION_ATTEMPT: int = state.get("attempts", 0) + 1
        errors = []
        mapping_errors = []

        # Debug logging
        logger = get_validation_logger()
        logger.debug(
            f"🔍 VALIDATION DEBUG - Starting validation for task: {state.get('task', 'unknown')}"
        )
        logger.debug(
            f"🔍 VALIDATION DEBUG - Statement: {state.get('statement', 'no statement')}"
        )
        logger.debug(f"🔍 VALIDATION DEBUG - Attempt: {GENERATION_ATTEMPT}")
        logger.debug(f"🔍 VALIDATION DEBUG - Max attempts: {max_attempts}")

        # Check for syntax errors
        syntax_error = validate_cypher_query_syntax(
            graph=graph, cypher_statement=state.get("statement", "")
        )

        errors.extend(syntax_error)

        # check for write clauses
        write_errors = validate_no_writes_in_cypher_query(state.get("statement", ""))
        errors.extend(write_errors)

        # Experimental feature for correcting relationship directions
        corrected_cypher = correct_cypher_query_relationship_direction(
            graph=graph, cypher_statement=state.get("statement", "")
        )

        # Use LLM to find additional potential errors and get the mapping for values
        llm_errors = await validate_cypher_query_with_llm(
            validate_cypher_chain=validate_cypher_chain,
            question=state.get("task", ""),
            graph=graph,
            cypher_statement=state.get("statement", ""),
        )
        errors.extend(llm_errors.get("errors", []))
        mapping_errors.extend(llm_errors.get("mapping_errors", []))

        # determine next node in workflow
        if (errors or mapping_errors) and GENERATION_ATTEMPT < max_attempts:
            next_action = "correct_cypher"
        elif GENERATION_ATTEMPT < max_attempts:
            next_action = "execute_cypher"
        elif (
            GENERATION_ATTEMPT == max_attempts
            and attempt_cypher_execution_on_final_attempt
        ):
            next_action = "execute_cypher"
        else:
            next_action = "__end__"

        return {
            "next_action_cypher": next_action,
            "statement": corrected_cypher,
            "errors": errors,
            "attempts": GENERATION_ATTEMPT,
            "cypher_steps": ["validate_cypher"],
        }

    return validate_cypher
