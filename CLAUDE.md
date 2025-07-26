# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Neo4j Text2Cypher package built with LangChain and LangGraph for creating agentic workflows that convert natural language questions into Cypher queries. The system uses a modular architecture with comprehensive error handling and validation.

## Development Commands

### Setup
- `make init` - Initialize development environment (equivalent to `poetry install --with dev,ui`)

### Testing
- `make test` - Run all tests with pytest
- `make test_unit` - Run unit tests only
- `poetry run pytest tests/unit -s` - Run unit tests with verbose output
- `poetry run pytest tests/unit/test_specific.py::test_function -s` - Run specific test

### Code Quality
- `make format` - Format code with ruff and fix import sorting
- `make clean` - Run ruff checks with auto-fix
- `make mypy` - Run type checking with mypy

### Applications
- `make streamlit file_path=example_apps/iqs_data_explorer/app-config.yml` - Launch Streamlit web app
- `make langgraph` - Start LangGraph Studio development server for workflow visualization
- `jupyter notebook example_apps/iqs_data_explorer/iqs_data_explorer_example.ipynb` - Run example notebook

## Core Architecture

The system follows a modular LangGraph workflow pattern:

### Main Workflow Components (in execution order)
1. **Guardrails** (`neo4j_text2cypher/components/guardrails/`) - Validates questions are within scope using graph schema
2. **Planner** (`neo4j_text2cypher/components/planner/`) - Breaks complex questions into sub-questions  
3. **Text2Cypher Pipeline** (`neo4j_text2cypher/components/text2cypher/`) - Multi-step process:
   - **Generation** - Creates Cypher using retrieval-augmented few-shot examples
   - **Validation** - Multi-layer validation (syntax, security, semantic)
   - **Correction** - Iterative error fixing with max attempt limits
   - **Execution** - Safe query execution with result gathering
4. **Summarize** (`neo4j_text2cypher/components/summarize/`) - Formats raw results into natural language
5. **Final Answer** (`neo4j_text2cypher/components/final_answer/`) - Formats output and updates history

### Workflow State Management

The workflow uses typed state objects that flow through the graph:
- **InputState** - Initial user input (question, data, history)
- **OverallState** - Complete workflow state including all intermediate data
- **GuardrailsState** - Tracks scope validation results
- **PlannerState** - Contains decomposed tasks array
- **Text2CypherState** - Individual task processing state
- **CypherOutputState** - Query execution results
- **OutputState** - Final formatted response

States are defined in `neo4j_text2cypher/components/state.py` and component-specific states in their respective directories.

### Key Files
- `neo4j_text2cypher/workflows/neo4j_text2cypher_workflow.py` - Main workflow orchestration
- `neo4j_text2cypher/workflows/single_agent/text2cypher.py` - Text2Cypher subgraph implementation
- `neo4j_text2cypher/workflows/edges.py` - Conditional routing logic
- `neo4j_text2cypher/agent.py` - LangGraph Studio configuration
- `neo4j_text2cypher/components/state.py` - Workflow state management
- `neo4j_text2cypher/utils/config.py` - Unified configuration system
- `neo4j_text2cypher/utils/schema_utils.py` - Neo4j schema extraction utilities

### Configuration System
Applications use YAML configuration files (see `example_apps/iqs_data_explorer/app-config.yml`) that combine:
- Neo4j connection settings (supports env vars → config → defaults hierarchy)
- Streamlit UI configuration (title, description, example questions)
- Few-shot query examples for Cypher generation
- Debug configuration for component-level logging

### Retrieval System
- `neo4j_text2cypher/retrievers/config_retriever.py` - Config-based example retrieval
- Examples are loaded from YAML configuration files
- Used for RAG-enhanced Cypher generation with few-shot prompting

### Error Handling
- Custom exceptions in `neo4j_text2cypher/exceptions.py`
- Max attempt limits for query generation/correction cycles
- Optional "attempt_cypher_execution_on_final_attempt" for graceful degradation
- Comprehensive validation layers catch syntax, security, and semantic issues

## Technology Stack
- **LangChain** - LLM and database connections
- **LangGraph** - Workflow orchestration and state management
- **Neo4j** - Graph database with neo4j-driver and langchain-neo4j
- **Poetry** - Dependency management
- **Streamlit** - Web UI framework
- **OpenAI GPT-4o** - Default LLM (configurable)
- **Python 3.10+** - Required Python version

## Environment Setup
Copy `.env.example` to `.env` and configure:
- `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `NEO4J_URI`, `NEO4J_DATABASE`
- `OPENAI_API_KEY`

Connection parameters follow this hierarchy: environment variables → config file → defaults