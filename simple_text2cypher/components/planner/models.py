from typing import List

from pydantic import BaseModel, Field

from simple_text2cypher.components.models import Task


class PlannerOutput(BaseModel):
    tasks: List[Task] = Field(
        default=[],
        description="A list of tasks that must be complete to satisfy the input question.",
    )
