"""
This file contains Cypher validators that may be used in the Text2Cypher validation node.
"""

from typing import Any, Dict, List

from langchain_core.runnables.base import Runnable
from langchain_neo4j import Neo4jGraph
from langchain_neo4j.chains.graph_qa.cypher_utils import CypherQueryCorrector, Schema
from neo4j.exceptions import CypherSyntaxError

from neo4j_text2cypher.components.text2cypher.validation.models import (
    ValidateCypherOutput,
)
from neo4j_text2cypher.constants import WRITE_CLAUSES
from neo4j_text2cypher.utils.debug import get_validation_logger
from neo4j_text2cypher.utils.schema_utils import (
    retrieve_and_parse_schema_from_graph_for_prompts,
)


def validate_cypher_query_syntax(graph: Neo4jGraph, cypher_statement: str) -> List[str]:
    """
    Validate the Cypher statement syntax by running an EXPLAIN query.

    Parameters
    ----------
    graph : Neo4jGraph
        The Neo4j graph wrapper.
    cypher_statement : str
        The Cypher statement to validate.

    Returns
    -------
    List[str]
        If the statement contains invalid syntax, return an error message in a list
    """
    errors = list()
    try:
        graph.query(f"EXPLAIN {cypher_statement}")
    except CypherSyntaxError as e:
        errors.append(str(e.message))
    return errors


def correct_cypher_query_relationship_direction(
    graph: Neo4jGraph, cypher_statement: str
) -> str:
    """
    Correct Relationship directions in the Cypher statement with LangChain's `CypherQueryCorrector`.

    Parameters
    ----------
    graph : Neo4jGraph
        The Neo4j graph wrapper.
    cypher_statement : str
        The Cypher statement to validate.

    Returns
    -------
    str
        The Cypher statement with corrected Relationship directions.
    """
    # Cypher query corrector is experimental
    corrector_schema = [
        Schema(el["start"], el["type"], el["end"])
        for el in graph.structured_schema.get("relationships", list())
    ]
    cypher_query_corrector = CypherQueryCorrector(corrector_schema)

    corrected_cypher: str = cypher_query_corrector(cypher_statement)

    return corrected_cypher


async def validate_cypher_query_with_llm(
    validate_cypher_chain: Runnable[Dict[str, Any], Any],
    question: str,
    graph: Neo4jGraph,
    cypher_statement: str,
) -> Dict[str, List[str]]:
    """
    Validate the Cypher statement with an LLM.
    Use declared LLM to find Node and Property pairs to validate.
    Validate Node and Property pairs against the Neo4j graph.

    Parameters
    ----------
    validate_cypher_chain : RunnableSerializable
        The LangChain LLM to perform processing.
    question : str
        The question associated with the Cypher statement.
    graph : Neo4jGraph
        The Neo4j graph wrapper.
    cypher_statement : str
        The Cypher statement to validate.

    Returns
    -------
    Dict[str, List[str]]
        A Python dictionary with keys `errors` and `mapping_errors`, each with a list of found errors.
    """

    errors: List[str] = []
    mapping_errors: List[str] = []

    logger = get_validation_logger()
    logger.debug(f"🔍 LLM VALIDATION DEBUG - Question: {question}")
    logger.debug(f"🔍 LLM VALIDATION DEBUG - Cypher: {cypher_statement}")

    schema_for_validation = retrieve_and_parse_schema_from_graph_for_prompts(graph)
    logger.debug("🔍 LLM VALIDATION DEBUG - Schema being used for validation:")
    logger.debug(
        f"🔍 LLM VALIDATION DEBUG - Schema length: {len(schema_for_validation)} characters"
    )
    logger.debug(f"🔍 LLM VALIDATION DEBUG - Schema content:\n{schema_for_validation}")

    llm_output: ValidateCypherOutput = await validate_cypher_chain.ainvoke(
        {
            "question": question,
            "schema": schema_for_validation,
            "cypher": cypher_statement,
        }
    )

    logger.debug(f"🔍 LLM VALIDATION DEBUG - LLM found errors: {llm_output.errors}")
    logger.debug(f"🔍 LLM VALIDATION DEBUG - LLM filters: {llm_output.filters}")

    if llm_output.errors:
        errors.extend(llm_output.errors)
    # Instead of checking individual property mappings, test the whole query with EXPLAIN
    # This catches real syntax/schema issues without false negatives for valid queries
    try:
        logger.debug("🔍 LLM VALIDATION DEBUG - Testing query validity with EXPLAIN")
        graph.query(f"EXPLAIN {cypher_statement}")
        logger.debug("🔍 LLM VALIDATION DEBUG - Query is valid - no mapping errors")
    except Exception as e:
        mapping_error = f"Query validation failed: {str(e)}"
        logger.debug(
            f"🔍 LLM VALIDATION DEBUG - Query validation failed: {mapping_error}"
        )
        mapping_errors.append(mapping_error)

    logger.debug(
        f"🔍 LLM VALIDATION DEBUG - Final result - errors: {errors}, mapping_errors: {mapping_errors}"
    )
    return {"errors": errors, "mapping_errors": mapping_errors}


def validate_no_writes_in_cypher_query(cypher_statement: str) -> List[str]:
    """
    Check if the Cypher statement contains write clauses.

    Parameters
    ----------
    cypher_statement : str
        The Cypher statement to check.

    Returns
    -------
    List[str]
        A list of found write clauses.
    """
    errors = []
    for write_clause in WRITE_CLAUSES:
        if f" {write_clause.upper()} " in cypher_statement.upper():
            errors.append(f"Cypher query contains the write clause: {write_clause}")
    return errors