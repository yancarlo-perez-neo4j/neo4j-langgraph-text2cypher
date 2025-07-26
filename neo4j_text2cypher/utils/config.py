"""Unified configuration loader for Neo4j Text2Cypher applications."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, Field


class Neo4jConfig(BaseModel):
    """Neo4j connection configuration."""

    database: str = Field(default="neo4j", description="Neo4j database name")
    uri: Optional[str] = Field(default=None, description="Neo4j connection URI")
    username: str = Field(default="neo4j", description="Neo4j username")
    password: Optional[str] = Field(default=None, description="Neo4j password")
    enhanced_schema: bool = Field(default=True, description="Enable enhanced schema")


class StreamlitUIConfig(BaseModel):
    """Streamlit UI configuration."""

    title: str = Field(description="Application title")
    scope_description: str = Field(description="Description of what the app can answer")
    example_questions: List[str] = Field(
        default=[], description="Example questions for the UI"
    )


class ExampleQuery(BaseModel):
    """Individual example query with question and CQL."""

    question: str = Field(description="Natural language question")
    cql: str = Field(description="Corresponding Cypher query")


class DebugConfig(BaseModel):
    """Debug logging configuration."""

    validation: bool = Field(
        default=False, description="Enable validation debug logging"
    )
    routing: bool = Field(default=False, description="Enable routing debug logging")
    planner: bool = Field(default=False, description="Enable planner debug logging")


class UnifiedAppConfig(BaseModel):
    """Unified application configuration combining all settings."""

    streamlit_ui: StreamlitUIConfig = Field(description="Streamlit UI settings")
    neo4j: Neo4jConfig = Field(description="Neo4j connection settings")
    example_queries: List[ExampleQuery] = Field(
        default=[], description="Example question-cypher pairs"
    )
    visualization_examples: Optional[List[ExampleQuery]] = Field(
        default=[], description="Visualization-specific example question-cypher pairs"
    )
    debug: DebugConfig = Field(
        default_factory=DebugConfig, description="Debug logging settings"
    )


class ConfigLoader:
    """Loads and merges configuration from YAML file and environment variables."""

    def __init__(self, config_path: Union[str, Path]):
        """Initialize with path to app config YAML file."""
        self.config_path = Path(config_path)
        self._raw_config: Optional[Dict[str, Any]] = None
        self._unified_config: Optional[UnifiedAppConfig] = None

    def load_config(self) -> UnifiedAppConfig:
        """Load and parse the unified configuration."""
        if self._unified_config is not None:
            return self._unified_config

        # Load YAML file
        with open(self.config_path, "r", encoding="utf-8") as f:
            self._raw_config = yaml.safe_load(f)

        # Extract sections
        streamlit_config = self._raw_config.get("streamlit_ui", {})
        neo4j_config = self._raw_config.get("neo4j", {})
        example_queries = self._raw_config.get("example_queries", [])
        visualization_examples = self._raw_config.get("visualization_examples", [])
        debug_config = self._raw_config.get("debug", {})

        # Merge Neo4j config with environment variables
        merged_neo4j_config = self._merge_neo4j_config(neo4j_config)

        # Merge debug config with environment variables
        merged_debug_config = self._merge_debug_config(debug_config)

        # Parse example queries (handle both new and legacy formats)
        parsed_queries = self._parse_example_queries(example_queries)
        parsed_viz_examples = self._parse_example_queries(visualization_examples)

        # Create unified config
        self._unified_config = UnifiedAppConfig(
            streamlit_ui=StreamlitUIConfig(**streamlit_config),
            neo4j=Neo4jConfig(**merged_neo4j_config),
            example_queries=parsed_queries,
            visualization_examples=parsed_viz_examples,
            debug=DebugConfig(**merged_debug_config),
        )

        return self._unified_config

    def _merge_neo4j_config(self, yaml_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge YAML Neo4j config with environment variables."""
        # Start with defaults from environment
        merged_config = {
            "database": os.getenv("NEO4J_DATABASE", "neo4j"),
            "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            "enhanced_schema": True,
        }

        # Override with YAML config (app-specific settings take precedence)
        merged_config.update(yaml_config)

        return merged_config

    def _merge_debug_config(self, yaml_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge YAML debug config with environment variables."""
        # Environment variables override YAML config
        merged_config = {
            "validation": self._str_to_bool(
                os.getenv("DEBUG_VALIDATION", str(yaml_config.get("validation", False)))
            ),
            "routing": self._str_to_bool(
                os.getenv("DEBUG_ROUTING", str(yaml_config.get("routing", False)))
            ),
            "planner": self._str_to_bool(
                os.getenv("DEBUG_PLANNER", str(yaml_config.get("planner", False)))
            ),
        }

        return merged_config

    def _str_to_bool(self, value: str) -> bool:
        """Convert string to boolean."""
        return str(value).lower() in ("true", "1", "yes", "on")

    def _parse_example_queries(
        self, queries_data: List[Dict[str, Any]]
    ) -> List[ExampleQuery]:
        """Parse example queries from unified format."""
        if not queries_data:
            return []

        parsed_queries = []
        for query in queries_data:
            if isinstance(query, dict) and "question" in query and "cql" in query:
                parsed_queries.append(
                    ExampleQuery(question=query["question"], cql=query["cql"])
                )

        return parsed_queries

    def get_neo4j_connection_params(self) -> Dict[str, Any]:
        """Get Neo4j connection parameters from environment, falling back to config."""
        config = self.load_config()

        return {
            "url": os.getenv("NEO4J_URI", config.neo4j.uri),
            "username": os.getenv("NEO4J_USERNAME", config.neo4j.username),
            "password": os.getenv("NEO4J_PASSWORD", config.neo4j.password),
            "database": os.getenv("NEO4J_DATABASE", config.neo4j.database),
            "enhanced_schema": config.neo4j.enhanced_schema,
        }

    def get_streamlit_config(self) -> StreamlitUIConfig:
        """Get Streamlit UI configuration."""
        return self.load_config().streamlit_ui

    def get_example_queries(self) -> List[ExampleQuery]:
        """Get parsed example queries."""
        return self.load_config().example_queries
    
    def get_visualization_examples(self) -> List[ExampleQuery]:
        """Get parsed visualization example queries."""
        examples = self.load_config().visualization_examples
        return examples if examples is not None else []

    def get_debug_config(self) -> DebugConfig:
        """Get debug configuration."""
        return self.load_config().debug
