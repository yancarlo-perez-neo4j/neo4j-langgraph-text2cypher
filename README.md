# Neo4j Text2Cypher

A simplified Text2Cypher agent for Neo4j using LangGraph. This project demonstrates how to build a robust natural language to Cypher query system with guardrails, validation, and a clean modular architecture.

## Features

- **Text2Cypher Conversion**: Convert natural language questions to Cypher queries
- **Guardrails**: Validate questions are within scope before processing
- **Query Planning**: Break down complex questions into subtasks
- **Cypher Validation**: Rule-based and optional LLM-based validation
- **Error Correction**: Iterative correction of invalid Cypher queries
- **Streamlit UI**: Clean web interface for interaction
- **Jupyter Examples**: Complete notebook examples for learning

## Architecture

The system follows a modular LangGraph workflow:

```
Input → Guardrails → Planner → Text2Cypher → Gather Results → Summarize → Validate → Final Answer
```

### Core Components

- **Guardrails**: Ensures questions are in scope
- **Planner**: Breaks down complex questions into subtasks
- **Text2Cypher**: Generates, validates, corrects, and executes Cypher
- **Summarization**: Formats results in natural language
- **Final Answer Validation**: Quality check before response

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

### 3. Configure Your Examples

Edit `data/example/queries.yml` with question-Cypher pairs relevant to your graph:

```yaml
questions:
  - question: "How many customers do we have?"
    cypher: "MATCH (c:Customer) RETURN count(c) as customerCount"
  - question: "What products are available?"
    cypher: "MATCH (p:Product) RETURN p.name as productName LIMIT 10"
```

### 4. Run the Application

#### Streamlit Web App
```bash
make streamlit file_path=data/example/ui-config.json
```

#### Jupyter Notebook
```bash
jupyter notebook examples/simple_text2cypher_example.ipynb
```

#### Python Code
```python
from neo4j_text2cypher.workflows.neo4j_text2cypher_workflow import create_neo4j_text2cypher_workflow
from neo4j_text2cypher.retrievers.cypher_examples import YAMLCypherExampleRetriever
from langchain_neo4j import Neo4jGraph
from langchain_openai import ChatOpenAI

# Initialize components
graph = Neo4jGraph(enhanced_schema=True)
llm = ChatOpenAI(model="gpt-4o", temperature=0)
retriever = YAMLCypherExampleRetriever("data/example/queries.yml")

# Create workflow
agent = create_neo4j_text2cypher_workflow(
    llm=llm,
    graph=graph,
    cypher_example_retriever=retriever,
    scope_description="This answers questions about your graph database."
)

# Ask a question
response = await agent.ainvoke({
    "question": "How many nodes are in the database?",
    "data": [],
    "history": []
})

print(response["answer"])
```

## Configuration

### UI Configuration (`ui-config.json`)

```json
{
    "title": "Your App Name",
    "scope_description": "Description of what your app can answer",
    "cypher_query_yaml_file_path": "path/to/queries.yml",
    "example_questions": [
        "Example question 1",
        "Example question 2"
    ]
}
```

### Workflow Parameters

- `llm_cypher_validation`: Use LLM for validation (slower but more accurate)
- `max_attempts`: Maximum correction attempts for invalid Cypher
- `attempt_cypher_execution_on_final_attempt`: Execute even if validation fails

## Development

### Commands

```bash
make test           # Run tests
make format         # Format code
make mypy           # Type checking
make langgraph      # Start LangGraph Studio
```

### Project Structure

```
neo4j-text2cypher/
├── neo4j_text2cypher/
│   ├── components/          # LangGraph node components
│   │   ├── guardrails/      # Input validation
│   │   ├── planner/         # Question decomposition
│   │   ├── text2cypher/     # Core T2C logic
│   │   ├── summarize/       # Result formatting
│   │   └── final_answer/    # Output validation
│   ├── retrievers/          # Cypher example retrieval
│   ├── workflows/           # Main workflow definitions
│   └── ui/                  # Streamlit interface
├── data/example/            # Configuration and examples
├── examples/                # Jupyter notebooks
└── tests/                   # Test suite
```

## Customization

### Adding New Components

1. Create component in `neo4j_text2cypher/components/your_component/`
2. Implement `node.py` with your logic
3. Add to workflow in `workflows/neo4j_text2cypher_workflow.py`

### Custom Retrievers

Implement `BaseCypherExampleRetriever` for custom example sources:

```python
from neo4j_text2cypher.retrievers.cypher_examples.base import BaseCypherExampleRetriever

class MyRetriever(BaseCypherExampleRetriever):
    def get_examples(self, question: str, k: int = 5) -> List[Dict]:
        # Your custom logic here
        return examples
```

### Custom Validation

Extend the validation components in `components/text2cypher/validation/` to add domain-specific rules.

## Examples

See `examples/neo4j_text2cypher_example.ipynb` for a complete walkthrough including:
- Setup and initialization
- Workflow creation and visualization
- Example queries and results
- Customization tips

## Contributing

1. Follow the existing code style (ruff formatting)
2. Add tests for new functionality
3. Update documentation as needed
4. Ensure type hints are present

## License

Apache License, Version 2.0