import re

from langchain_neo4j import Neo4jGraph


def get_cypher_query_node_graph_schema() -> str:
    # dont precompile the string. this would break re.sub in utils.py
    return r"^(- \*\*CypherQuery\*\*[\s\S]+?)(^Relationship properties|- \*)"


def retrieve_and_parse_schema_from_graph_for_prompts(graph: Neo4jGraph) -> str:
    schema: str = graph.get_schema

    # remove any mention of CypherQuery nodes and their contents
    if "CypherQuery" in schema:
        return re.sub(
            get_cypher_query_node_graph_schema(), r"\2", schema, flags=re.MULTILINE
        )

    return schema
