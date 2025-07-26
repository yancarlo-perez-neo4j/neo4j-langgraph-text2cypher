"""
Detect if a user question requests visualization of graph data.
"""

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate


def create_visualization_detection_prompt() -> ChatPromptTemplate:
    """
    Create a prompt template for detecting visualization requests.
    
    Returns
    -------
    ChatPromptTemplate
        The prompt template for visualization detection.
    """
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an expert at understanding user intent for graph database queries.
                
Determine if the user wants a visual graph representation of the results.

Questions requesting visualization often include:
- Direct visualization keywords: 'visualize', 'show graph', 'display network', 'illustrate', 'render'
- Visual/display verbs with data: 'show', 'display', 'present', 'depict' (when referring to entities/relationships)
- Relationship exploration: 'show connections', 'display relationships', 'how are X and Y related', 'map the relationships'
- Path queries: 'show the path between', 'trace the connection', 'feedback paths'
- Network analysis: 'show the network', 'display the structure', 'graph of'
- Visualization context: 'see how', 'look at how', 'view the'

IMPORTANT: If a question starts with "Visualize" or contains "visualize", it's almost always TRUE.

However, NOT all questions about relationships need visualization:
- Counting: 'how many connections' → FALSE
- Aggregations: 'average number of relationships' → FALSE  
- Simple facts: 'is X connected to Y' → FALSE
- Lists without visual verbs: 'list all connections', 'what are the connections' → FALSE
- Statistical queries: 'percentage of', 'count of', 'number of' → FALSE

When in doubt, if the user explicitly uses "visualize" or similar visual verbs, return TRUE.

Respond with only TRUE or FALSE."""
            ),
            (
                "human",
                "Question: {question}\n\nDoes this question request graph visualization?"
            ),
        ]
    )


async def detect_visualization_request(
    llm: BaseChatModel,
    question: str
) -> bool:
    """
    Detect if a question requests graph visualization.
    
    Parameters
    ----------
    llm : BaseChatModel
        The language model to use for detection
    question : str
        The user's question
        
    Returns
    -------
    bool
        True if visualization is requested, False otherwise
    """
    # Keyword override - if question contains these keywords, always return True
    visualization_keywords = ['visualize', 'show graph', 'display graph', 'render graph']
    question_lower = question.lower()
    
    for keyword in visualization_keywords:
        if keyword in question_lower:
            return True
    
    # If no explicit keywords, use LLM detection
    try:
        prompt = create_visualization_detection_prompt()
        response = await llm.ainvoke(prompt.format_messages(question=question))
        
        # Parse response
        result = response.content.strip().upper()
        return result == "TRUE"
        
    except Exception as e:
        print(f"Error detecting visualization request: {e}")
        # Default to False on error - graceful degradation
        return False