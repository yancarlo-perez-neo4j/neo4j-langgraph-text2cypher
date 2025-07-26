"""
Enhanced generation node that detects and handles visualization requests.
"""

from typing import Any, Callable, Coroutine, Dict

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_neo4j import Neo4jGraph

from neo4j_text2cypher.components.text2cypher.generation.prompts import (
    create_text2cypher_generation_prompt_template,
)
from neo4j_text2cypher.components.text2cypher.state import CypherInputState
from neo4j_text2cypher.components.text2cypher.visualization_detector import (
    detect_visualization_request,
)
from neo4j_text2cypher.retrievers import ConfigCypherExampleRetriever


def create_visualization_prompt_template() -> ChatPromptTemplate:
    """
    Create a prompt template for visualization-aware Cypher generation.
    
    Returns
    -------
    ChatPromptTemplate
        The prompt template for visualization queries.
    """
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "Given an input question, convert it to a Cypher query. No pre-amble."
                    "Do not wrap the response in any backticks or anything else. Respond with a Cypher statement only!"
                    "Always include a LIMIT clause to prevent excessive results unless the question specifically asks for all results."
                    "\nIMPORTANT: This query is for VISUALIZATION. Return the actual nodes, relationships, or paths, not aggregated data."
                    "\nKeep results small for visualization - use LIMIT 10 unless specifically requested otherwise."
                    "\nFor example:"
                    "\n- Instead of: RETURN COUNT(n)"
                    "\n- Use: RETURN n"
                    "\n- Instead of: RETURN n.name, n.age"  
                    "\n- Use: RETURN n"
                    "\n- For paths: RETURN path or RETURN nodes(path), relationships(path)"
                ),
            ),
            (
                "human",
                (
                    """You are a Neo4j expert. Given an input question, create a syntactically correct Cypher query to run.
Do not wrap the response in any backticks or anything else. Begin with MATCH or WITH clauses only. Respond with a Cypher statement only!

IMPORTANT: This is a VISUALIZATION request. Return nodes, relationships, or paths that can be displayed as a graph.
Always end your query with LIMIT 10 unless the question specifically asks for all results or a different number.

Here is the schema information
{schema}

Below are examples of visualization questions and their corresponding graph-compatible Cypher queries:

{visualization_examples}

User input: {question}
Cypher query:"""
                ),
            ),
        ]
    )


def create_text2cypher_generation_node_with_viz(
    llm: BaseChatModel,
    graph: Neo4jGraph,
    cypher_example_retriever: ConfigCypherExampleRetriever,
) -> Callable[[CypherInputState], Coroutine[Any, Any, dict[str, Any]]]:
    """
    Create a generation node that handles visualization requests.
    
    Parameters
    ----------
    llm : BaseChatModel
        The language model to use
    graph : Neo4jGraph
        The Neo4j graph wrapper
    cypher_example_retriever : ConfigCypherExampleRetriever
        The retriever for few-shot examples
        
    Returns
    -------
    Callable
        The generation node function
    """
    # Standard generation prompt
    standard_prompt = create_text2cypher_generation_prompt_template()
    standard_chain = standard_prompt | llm | StrOutputParser()
    
    # Visualization generation prompt
    viz_prompt = create_visualization_prompt_template()
    viz_chain = viz_prompt | llm | StrOutputParser()

    async def generate_cypher(state: CypherInputState) -> Dict[str, Any]:
        """
        Generates a cypher statement based on the provided schema and user input.
        Detects if visualization is requested and adjusts the generation accordingly.
        """
        task = state.get("task", "")
        examples: str = cypher_example_retriever.get_examples()
        
        # Detect if visualization is requested
        visualization_requested = await detect_visualization_request(llm, task)
        
        # Choose the appropriate examples and chain
        if visualization_requested:
            # Use visualization examples
            viz_examples: str = cypher_example_retriever.get_visualization_examples()
            generated_cypher = await viz_chain.ainvoke(
                {
                    "question": task,
                    "visualization_examples": viz_examples,
                    "schema": graph.schema,
                }
            )
        else:
            # Use standard examples
            standard_examples: str = cypher_example_retriever.get_examples()
            generated_cypher = await standard_chain.ainvoke(
                {
                    "question": task,
                    "fewshot_examples": standard_examples,
                    "schema": graph.schema,
                }
            )

        steps = state.get("prev_steps", list()) + ["generate_cypher"]
        
        return {
            "statement": generated_cypher,
            "cypher_steps": steps,
            "visualization_requested": visualization_requested
        }

    return generate_cypher