# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Neo4j Text2Cypher is a LangGraph-based agentic workflow system that converts natural language questions into Cypher queries for Neo4j databases. The system provides production-ready workflows with comprehensive error handling, validation, and conversation history support.

## Common Development Commands

```bash
# Setup and dependencies
make init                    # Initialize development environment
poetry install              # Install dependencies manually

# Code quality
make format                  # Run ruff formatter
make mypy                   # Type checking
make test                   # Run all tests
make test_unit              # Run unit tests only

# Running applications
make streamlit file_path=example_apps/iqs_data_explorer/app-config.yml  # Web interface
make langgraph              # Start LangGraph Studio development server

# Development workflow
poetry run python -m pytest tests/unit/  # Run specific test directory
poetry run ruff check --fix  # Auto-fix linting issues
```

## Architecture Overview

### Core Pipeline Flow
The system follows a modular LangGraph pipeline:

1. **Guardrails** → Question scope validation using graph schema
2. **Planner** → Multi-question decomposition and conversation history resolution  
3. **Text2Cypher** → Generation → Validation → Correction → Execution
4. **Summarize** → Natural language response formatting
5. **Final Answer Validation** → Quality assurance with retry loops

### Key Components Structure

- `neo4j_text2cypher/components/` - LangGraph nodes implementing pipeline stages
- `neo4j_text2cypher/workflows/` - Workflow definitions and graph construction
- `neo4j_text2cypher/retrievers/` - Few-shot example retrieval systems
- `neo4j_text2cypher/ui/` - Streamlit web interface
- `example_apps/` - Reference implementations with app-config.yml files

### State Management
- All components use shared state models (`State`, `Text2CypherState`)
- Immutable state flow through LangGraph pipeline
- Conversation history tracked via `HistoryRecord` and `CypherHistoryRecord`

## Configuration System

### Application Configuration
Apps are configured via YAML files (e.g., `example_apps/iqs_data_explorer/app-config.yml`):
- Neo4j database connection settings
- UI configuration (title, examples, behavior)
- Few-shot Cypher examples for domain-specific training
- Component-specific settings (validation modes, attempt limits)

### Environment Variables
Required in `.env` file:
- `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`
- `OPENAI_API_KEY`
- Optional: `LANGCHAIN_API_KEY` for tracing

## Important Patterns

### Error Handling & Validation
- Multi-layer Cypher validation: syntax → security → semantic → LLM-based
- Iterative correction with configurable attempt limits
- Graceful degradation with optional unsafe execution on final attempt

### Conversation History
- Planner rewrites follow-up questions to be self-contained
- Memory management keeps last 5-10 exchanges
- Context resolution handles ambiguous references

### Example Retrieval
- Unified configuration supports both YAML and vector store retrievers
- Few-shot examples are domain-specific and configured per app
- Retrieval-augmented generation for better Cypher quality

## Testing Strategy

- Unit tests focus on individual components in isolation
- Integration tests validate full pipeline workflows
- Test configuration uses separate test databases
- Pytest fixtures provide reusable test data and mocks

## LangGraph Studio Integration

Use `make langgraph` to start the development server for visual workflow debugging. The graph definition in `agent.py` provides the studio visualization, while `langgraph.json` contains studio configuration.