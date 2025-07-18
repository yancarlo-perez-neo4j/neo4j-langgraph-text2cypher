"""Configuration-based Cypher example retriever."""

from typing import Any, List

from pydantic import Field

from neo4j_text2cypher.retrievers.cypher_examples.base import BaseCypherExampleRetriever
from neo4j_text2cypher.utils.config import ConfigLoader, ExampleQuery


class ConfigCypherExampleRetriever(BaseCypherExampleRetriever):
    """Retriever that loads examples from app configuration."""
    
    config_loader: ConfigLoader = Field(
        description="Unified app config loader"
    )
    
    def __init__(self, config_path: str, **kwargs):
        """Initialize with path to app config file."""
        config_loader = ConfigLoader(config_path)
        super().__init__(config_loader=config_loader, **kwargs)
    
    def get_examples(self, *args: Any, **kwargs: Any) -> str:
        """Get formatted example queries from the configuration."""
        example_queries = self.config_loader.get_example_queries()
        return self._format_examples_list(example_queries)
    
    def _format_examples_list(self, examples: List[ExampleQuery]) -> str:
        """Format example queries for use in prompts."""
        return ("\n" * 2).join([
            f"Question: {example.question}\nCypher:{self._format_cypher_for_example(example.cql)}"
            for example in examples
        ])
    
