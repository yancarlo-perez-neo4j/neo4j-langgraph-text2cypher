from typing import Optional

from pydantic import BaseModel, Field

from .text2cypher.state import CypherOutputState


class Task(BaseModel):
    question: str = Field(..., description="The question to be addressed.")
    parent_task: str = Field(
        ..., description="The parent task this task is derived from."
    )
    data: Optional[CypherOutputState] = Field(
        default=None, description="The Cypher query result details."
    )

    @property
    def is_complete(self) -> bool:
        return self.data is not None
