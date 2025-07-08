# Neo4j Text2Cypher

This repository contains the `neo4j-text2cypher` package which may be used to create off-the-shelf agentic workflows built for Neo4j. The purpose of this repo is to provide foundational agents and workflows that may function with any underlying Neo4j graph. While these workflows should function well on their own - it is expected that they will be augmented to serve more specific use cases once pulled into other projects.

This package uses the [LangChain](https://github.com/langchain-ai) library for LLM and database connections.

This package uses [LangGraph](https://github.com/langchain-ai/langgraph) for workflow orchestration.

This project and structure is based on the work by Alex Gilmore and the repository can be found [here](https://github.com/neo4j-field/ps-genai-agents)

## Contents

This repository contains
* Predefined agentic workflow for Text2Cypher usage
* Streamlit Demo Application
* Example Notebook

## Architecture

The system follows a modular LangGraph workflow with comprehensive error handling:

### Core Components

- **Guardrails**: Ensures questions are within scope using graph schema validation
- **Planner**: Breaks down complex questions into sub-questions
- **Text2Cypher Pipeline**: 
  - **Generation**: Creates Cypher using retrieval-augmented few-shot examples
  - **Validation**: Multi-layer validation (syntax, security, semantic correctness)
  - **Correction**: Iterative error fixing with max attempt limits
  - **Execution**: Safe query execution with result gathering
- **Summarization**: Formats raw results into natural language responses
- **Final Answer Validation**: Quality assurance with conditional retry loops

### Workflow Diagram

![Detailed Workflow Diagram](docs/images/workflow_diagram_detailed.png)

*The diagram above shows the complete LangGraph workflow with all components and decision points, including the detailed Text2Cypher pipeline with generation, validation, correction, and execution steps.*

## Quick Start

### 1. Installation

```bash
git clone <repository-url>
cd neo4j-text2cypher
make init  # or poetry install --with dev,ui
```

### 2. Environment Setup

Copy the environment template and add your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your Neo4j and OpenAI credentials:

```env
NEO4J_USERNAME="neo4j"
NEO4J_PASSWORD="your_password"
NEO4J_URI="bolt://localhost:7687"
NEO4J_DATABASE="neo4j"
OPENAI_API_KEY="sk-your_openai_key"
```

### 3. Configure Your Application

Create or edit your application configuration file (e.g., `example_apps/iqs_data_explorer/app-config.yml`):

```yaml
neo4j:
  database: "your_database_name"
  # uri: "bolt://localhost:7687"  # Optional override

streamlit_ui:
  title: "Your App Name"
  scope_description: "Description of what your app can answer"
  example_questions:
    - "How many customers do we have?"
    - "What products are available?"

example_queries:
  - question: "How many customers do we have?"
    cql: "MATCH (c:Customer) RETURN count(c) as customerCount"
  - question: "What products are available?"
    cql: "MATCH (p:Product) RETURN p.name as productName LIMIT 10"
```

The configuration file combines all settings in one place:
- **Neo4j settings**: Database connection details
- **UI configuration**: App title, description, and example questions
- **Query examples**: Question-Cypher pairs for few-shot learning

### 4. Run the Application

#### Streamlit Web App
```bash
make streamlit file_path=example_apps/iqs_data_explorer/app-config.yml
```

#### Jupyter Notebook
```bash
jupyter notebook example_apps/iqs_data_explorer/iqs_data_explorer_example.ipynb
```

### Project Structure

```
neo4j-text2cypher/
├── neo4j_text2cypher/           # Main package
│   ├── components/              # LangGraph node components
│   │   ├── guardrails/          # Input validation and scope checking
│   │   ├── planner/             # Question decomposition
│   │   ├── text2cypher/         # Core T2C pipeline
│   │   │   ├── generation/      # Cypher query generation
│   │   │   ├── validation/      # Multi-layer validation
│   │   │   ├── correction/      # Error correction
│   │   │   └── execution/       # Safe query execution
│   │   ├── gather_cypher/       # Result collection
│   │   ├── summarize/           # Natural language formatting
│   │   ├── final_answer/        # Final output generation
│   │   └── validate_final_answer/ # Answer quality validation
│   ├── retrievers/              # Example retrieval systems
│   │   └── cypher_examples/     # Few-shot example retrievers
│   ├── workflows/               # LangGraph workflow definitions
│   ├── ui/                      # Streamlit web interface
│   └── utils/                   # Utility functions
├── example_apps/                # Example applications
│   └── iqs_data_explorer/       # Sample app with configuration
├── tests/                       # Comprehensive test suite
│   ├── unit/                    # Unit tests for components
│   └── conftest.py             # Test configuration
└── docs/                        # Documentation (if any)
```

## Examples

See `example_apps/iqs_data_explorer/iqs_data_explorer_example.ipynb` for a complete walkthrough including:
- Environment setup and initialization
- Workflow creation and configuration
- Example queries with step-by-step execution
- Result analysis and customization tips
- Testing different validation approaches

The example demonstrates a real-world use case with Honda/Acura vehicle feedback data, showing:
- Complex multi-hop queries
- Filtering and aggregation patterns
- Natural language result formatting
- Error handling and correction

## License
Apache License, Version 2.0