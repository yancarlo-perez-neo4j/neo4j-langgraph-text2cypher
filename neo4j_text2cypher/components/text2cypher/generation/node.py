"""
This code is based on content found in the LangGraph documentation: https://python.langchain.com/docs/tutorials/graph/#advanced-implementation-with-langgraph
"""

from typing import Any, Callable, Coroutine, Dict, List

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_neo4j import Neo4jGraph

from neo4j_text2cypher.components.text2cypher.generation.prompts import (
    create_text2cypher_generation_prompt_template,
)
from neo4j_text2cypher.retrievers.cypher_examples.base import BaseCypherExampleRetriever
from neo4j_text2cypher.components.text2cypher.state import CypherInputState

generation_prompt = create_text2cypher_generation_prompt_template()


def format_conversation_history_for_cypher(history: List[Dict[str, Any]]) -> str:
    """
    Format conversation history for the text2cypher generation prompt.
    
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
        
        # Include cypher queries for additional context
        if record.get('cyphers'):
            formatted_history += f"   Cypher queries used:\n"
            for cypher in record['cyphers']:
                formatted_history += f"   - {cypher['statement']}\n"
    
    return formatted_history


def create_text2cypher_generation_node(
    llm: BaseChatModel,
    graph: Neo4jGraph,
    cypher_example_retriever: BaseCypherExampleRetriever,
) -> Callable[[CypherInputState], Coroutine[Any, Any, dict[str, Any]]]:
    text2cypher_chain = generation_prompt | llm | StrOutputParser()

    async def generate_cypher(state: CypherInputState) -> Dict[str, Any]:
        """
        Generates a cypher statement based on the provided schema and user input
        """

        examples: str = cypher_example_retriever.get_examples(
            **{"query": state.get("task", ""), "k": 8}
        )

        # Format conversation history for the prompt
        # Note: The planner already resolves context references, so detailed history is not needed here
        conversation_history = "No previous conversation history."

        # print("\n\nExamples: ", examples, "\n\n")
        generated_cypher = await text2cypher_chain.ainvoke(
            {
                "question": state.get("task", ""),
                "fewshot_examples": examples,
                "schema": graph.schema,
                "conversation_history": conversation_history,
            }
        )
        # print("GENERATED CYPHER: ", generated_cypher, "\n\n")
        steps = state.get("prev_steps", list()) + ["generate_cypher"]
        return {"statement": generated_cypher, "cypher_steps": steps}

    return generate_cypher
