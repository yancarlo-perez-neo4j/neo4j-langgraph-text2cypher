from typing import Any, Dict, List

import yaml
from pydantic import Field

from neo4j_text2cypher.retrievers.cypher_examples.base import BaseCypherExampleRetriever


class YAMLCypherExampleRetriever(BaseCypherExampleRetriever):
    cypher_query_yaml_file_path: str = Field(
        description="The local file path to a YAML file containing question and Cypher query pairs."
    )

    def get_examples(self, *args: Any, **kwargs: Any) -> str:
        unformatted_examples = self._get_example_queries_from_yaml()

        return self._format_examples_list(unformatted_examples)

    def _format_examples_list(self, unformatted_examples: List[Dict[str, str]]) -> str:
        return ("\n" * 2).join(
            [
                f"Question: {el['question']}\nCypher:{el['cql']}"
                for el in unformatted_examples
            ]
        )

    def _get_example_queries_from_yaml(self) -> List[Dict[str, str]]:
        """
        Format the queries to be used in text2cypher.
        Expects unified format with 'example_queries' key and 'cql' field.
        """

        with open(self.cypher_query_yaml_file_path) as f:
            try:
                yaml_data = yaml.safe_load(f)
                queries = yaml_data.get("example_queries", [])
            except yaml.YAMLError as exc:
                print(exc)
                queries = []
        
        formatted_queries = []
        for q in queries:
            if "cql" in q and "question" in q:
                formatted_queries.append({
                    "question": q["question"],
                    "cql": self._format_cypher_for_example(q["cql"]),
                })
        
        return formatted_queries

    def _format_cypher_for_example(self, cypher: str) -> str:
        """
        Formats Cypher for use in LangChain's Example Templates.
        This involves replacing '{' with '{{' and '}' with '}}'.
        """

        cypher = cypher.replace("{", "{{")
        return cypher.replace("}", "}}")
