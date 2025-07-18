"""
This code is based on content found in the LangGraph documentation: https://python.langchain.com/docs/tutorials/graph/#advanced-implementation-with-langgraph
"""

from langchain_core.prompts import ChatPromptTemplate


def create_text2cypher_generation_prompt_template() -> ChatPromptTemplate:
    """
    Create a Text2Cypher generation prompt template.

    Returns
    -------
    ChatPromptTemplate
        The prompt template.
    """
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "Given an input question, convert it to a Cypher query. No pre-amble."
                    "Do not wrap the response in any backticks or anything else. Respond with a Cypher statement only!"
                    "Always include a LIMIT clause to prevent excessive results unless the question specifically asks for all results."
                ),
            ),
            (
                "human",
                (
                    """You are a Neo4j expert. Given an input question, create a syntactically correct Cypher query to run.
Do not wrap the response in any backticks or anything else. Begin with MATCH or WITH clauses only. Respond with a Cypher statement only!

IMPORTANT: Always end your query with LIMIT 100 unless the question specifically asks for all results or a different number.

IMPORTANT: If the current question contains references like "those", "them", "it", "that", or similar pronouns, 
use the conversation history to understand what these references mean. Look at previous questions and answers 
to determine the context and generate the appropriate Cypher query.

Here is the schema information
{schema}

Below are a number of examples of questions and their corresponding Cypher queries.

{fewshot_examples}

{conversation_history}

User input: {question}
Cypher query:"""
                ),
            ),
        ]
    )
