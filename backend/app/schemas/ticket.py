from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class TicketCreate(BaseModel):
    title: str = Field(min_length=4, max_length=180)
    customer: str = Field(min_length=2, max_length=120)
    body: str = Field(min_length=20)


class ReviewDecision(BaseModel):
    decision: Literal["approved", "rejected"]
    reviewer: str = Field(min_length=2, max_length=120)
    notes: str = Field(default="", max_length=600)


class TicketRead(BaseModel):
    id: int
    title: str
    customer: str
    body: str
    category: str | None
    priority: str | None
    risk: str | None
    status: str
    draft_response: str | None
    state_history: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
