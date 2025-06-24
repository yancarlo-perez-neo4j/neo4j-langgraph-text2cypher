"""
This code is based on content found in the LangGraph documentation: https://python.langchain.com/docs/tutorials/graph/#advanced-implementation-with-langgraph
"""

from typing import Literal

from pydantic import BaseModel, Field


class GuardrailsOutput(BaseModel):
    decision: Literal["end", "planner"] = Field(
        description="Decision on whether the question is related to the graph contents."
    )
