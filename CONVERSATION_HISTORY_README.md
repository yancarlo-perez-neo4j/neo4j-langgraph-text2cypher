# Conversation History Implementation Guide

This document explains how conversation history is implemented in the Neo4j Text2Cypher LangGraph system to enable follow-up questions and contextual conversations.

## Overview

The conversation history feature allows users to ask follow-up questions that reference previous context, such as:
- **Initial**: "How many Honda Civic responses are there?"
- **Follow-up**: "How many of those are from women?" (understands "those" refers to Honda Civic responses)

## Data Structure

### HistoryRecord
```python
class HistoryRecord(TypedDict):
    """Information that may be relevant to future user questions."""
    question: str                        # Original user question
    answer: str                          # System's response
    cyphers: List[CypherHistoryRecord]   # List of cypher executions for this Q&A
```

### CypherHistoryRecord  
```python
class CypherHistoryRecord(TypedDict):
    """A simplified representation of the CypherOutputState"""
    task: str                      # The specific task/sub-question
    statement: str                 # Generated Cypher query
    records: List[Dict[str, Any]]  # Actual query results (not count)
```

### State Integration
The conversation history is integrated into the LangGraph state system:

```python
class InputState(TypedDict):
    question: str
    data: List[Dict[str, Any]]
    history: Annotated[List[HistoryRecord], update_history]  # Previous Q&A pairs
    
class OverallState(TypedDict):
    question: str
    tasks: Annotated[List[Task], add]
    next_action: str
    cyphers: Annotated[List[CypherOutputState], add]
    summary: str
    steps: Annotated[List[Any], add]
    history: Annotated[List[HistoryRecord], update_history]  # Flows through workflow
```

## Implementation Architecture

### 1. History Storage (Streamlit)
**Location**: `neo4j_text2cypher/ui/components/chat.py`

```python
def convert_streamlit_messages_to_history() -> List[HistoryRecord]:
    """Convert Streamlit session messages to HistoryRecord format"""
    history = []
    messages = st.session_state.get("messages", [])
    
    # Process messages in pairs (user question + assistant answer)
    for i in range(0, len(messages) - 1, 2):
        user_msg = messages[i]
        assistant_msg = messages[i + 1]
        
        # Handle LangGraph AddableValuesDict objects
        if hasattr(assistant_content, 'get') and not isinstance(assistant_content, (str, dict)):
            assistant_content = dict(assistant_content)
        
        # Handle case where assistant_content might be a string (error messages)
        if isinstance(assistant_content, str):
            answer = assistant_content
            cyphers = []
        else:
            answer = assistant_content.get("answer", "")
            cypher_states = assistant_content.get("cyphers", [])
            
            # Convert cypher states to CypherHistoryRecord format
            cyphers = []
            for cypher_state in cypher_states:
                cypher_record = CypherHistoryRecord(
                    task=cypher_state.get("task", ""),
                    statement=cypher_state.get("statement", ""),
                    records=cypher_state.get("records", [])
                )
                cyphers.append(cypher_record)
        
        history.append(HistoryRecord(
            question=user_msg["content"],
            answer=answer,
            cyphers=cyphers
        ))
    
    return history
```

### 2. History Injection (Workflow Entry)
**Location**: `neo4j_text2cypher/ui/components/chat.py`

The history is injected into the workflow at the entry point:

```python
async def chat_interface():
    # Convert session messages to structured history
    conversation_history = convert_streamlit_messages_to_history()
    
    # Create input state with history
    input_state = InputState(
        question=user_input,
        data=[],
        history=conversation_history[-10:]  # Keep last 10 exchanges
    )
    
    # Execute workflow with history context
    result = await workflow.ainvoke(input_state)
```

### 3. History Processing (Planner)
**Location**: `neo4j_text2cypher/components/planner/node.py`

The planner uses conversation history to understand context and resolve references:

```python
def format_conversation_history(history: List[HistoryRecord]) -> str:
    """Format conversation history for planner prompt"""
    if not history:
        return "No previous conversation history."
    
    formatted_history = "Previous conversation history:\n\n"
    for i, record in enumerate(history, 1):
        formatted_history += f"{i}. Q: {record.question}\n"
        formatted_history += f"   A: {record.answer}\n\n"
    
    return formatted_history

async def planner_node(state: InputState) -> Dict[str, Any]:
    """Planning node that uses conversation history for context"""
    
    # Get and format conversation history
    history = state.get("history", [])
    conversation_history = format_conversation_history(history)
    
    # Generate tasks with historical context
    planner_output = await planner_chain.ainvoke({
        "question": state.get("question", ""),
        "conversation_history": conversation_history,
        "scope": scope_description
    })
    
    return {
        "tasks": planner_output.tasks,
        "history": history,  # Pass through workflow
        "next_action": "tool_selection"
    }
```

### 4. History in Prompts
**Location**: `neo4j_text2cypher/components/planner/prompts.py`

The planner prompt template includes conversation history:

```python
planner_user_prompt = """
You are a task planner for a Neo4j Text2Cypher system.

Conversation History:
{conversation_history}

Current Question: {question}

Based on the conversation history and current question, determine if this is:
1. A follow-up question that references previous context
2. A completely new question

If it's a follow-up question, rewrite it to be self-contained using the historical context.
Example:
- History: "Q: How many Honda Civic responses? A: 965 responses"  
- Follow-up: "How many of those are from women?"
- Rewritten: "How many Honda Civic responses are from women?"
"""
```

## Key Features

### 1. Context Resolution
The planner automatically resolves pronouns and references:
- "those" → "Honda Civic responses"
- "that vehicle" → "Honda Pilot"
- "the same model" → "RDX"

### 2. Memory Management
- **Size Limiting**: Only keeps last 10 conversation exchanges
- **Relevance Filtering**: Planner determines which history is relevant
- **Clean Formatting**: Structured format for LLM consumption

### 3. State Flow
History flows through the entire workflow:
```
InputState (with history) → Planner → Tool Selection → Text2Cypher → Summarizer → Final Answer
```

### 4. Technical History Tracking
Separate tracking for technical execution details:
- Generated Cypher queries
- Execution times
- Record counts
- Error information

## Usage in Different Components

### Summarizer
**Location**: `neo4j_text2cypher/components/summarize/node.py`

```python
def format_conversation_history_for_summary(history: List[HistoryRecord]) -> str:
    """Format history for summarization context"""
    if not history:
        return ""
    
    recent_history = history[-3:]  # Last 3 exchanges
    formatted = "Recent conversation context:\n"
    for record in recent_history:
        formatted += f"- Q: {record.question}\n  A: {record.answer}\n"
    
    return formatted
```

### Text2Cypher Generation
The conversation history can be used in Cypher generation for context-aware queries, though this is currently optional.

## Integration Points

### 1. Streamlit Session State
- History stored in `st.session_state.messages`
- Converted to structured format before workflow execution
- Handles LangGraph's AddableValuesDict objects

### 2. LangGraph State Management
- History flows through state as immutable data
- Each node can access and use history
- No modification of history during execution

### 3. Prompt Engineering
- History formatted for optimal LLM consumption
- Recent context prioritized
- Clean question/answer structure

## Benefits

1. **Natural Conversations**: Users can ask follow-up questions naturally
2. **Context Awareness**: System understands references to previous exchanges
3. **Improved UX**: No need to repeat context in every question
4. **Technical Tracking**: Detailed execution history for debugging
5. **Scalable**: Memory management prevents context overflow

## Configuration

Enable conversation history through the workflow configuration:

```python
# In your workflow setup
workflow = create_neo4j_text2cypher_workflow(
    llm=llm,
    graph=graph,
    scope_description=scope_description,
    cypher_example_retriever=retriever,
    # History is automatically enabled when InputState includes history
)
```

## Best Practices

1. **Limit History Size**: Keep only relevant recent exchanges (5-10)
2. **Clear Formatting**: Use structured format for LLM consumption
3. **Error Handling**: Handle malformed history gracefully
4. **Context Relevance**: Let the planner determine relevant history
5. **Performance**: Don't include history in every component, only where needed

This implementation provides a robust foundation for conversational AI with Neo4j and LangGraph, enabling natural follow-up questions while maintaining technical precision.