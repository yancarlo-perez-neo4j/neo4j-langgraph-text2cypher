from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ValidateFinalAnswerResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')
    valid: bool = Field(
        description="Whether the final answer sufficiently answers the provided question."
    )
    follow_up_question: Optional[str] = Field(
        description="A follow up question to ask that will gather the remaining information needed.",
        default=None,
    )
