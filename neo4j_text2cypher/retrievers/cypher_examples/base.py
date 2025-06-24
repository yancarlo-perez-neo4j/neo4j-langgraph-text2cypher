from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict


class BaseCypherExampleRetriever(BaseModel, ABC):
    """
    Abstract base class for an example retriever.
    Subclasses must implement the `get_examples` method.
    """

    model_config: ConfigDict = ConfigDict(**{"arbitrary_types_allowed": True})  # type: ignore[misc]

    @abstractmethod
    def get_examples(self, *args: Any, **kwargs: Any) -> str:
        """
        Retrieve relevant examples in string format that are ready to be injected into a prompt for few shot prompting.

        Returns
        -------
        str
            A list of examples as a string.
        """
        pass
