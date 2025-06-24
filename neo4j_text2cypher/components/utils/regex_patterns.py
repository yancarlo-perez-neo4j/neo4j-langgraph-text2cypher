def get_cypher_query_node_graph_schema() -> str:
    # dont precompile the string. this would break re.sub in utils.py
    return r"^(- \*\*CypherQuery\*\*[\s\S]+?)(^Relationship properties|- \*)"