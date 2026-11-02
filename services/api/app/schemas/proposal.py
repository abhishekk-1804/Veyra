from datetime import datetime
from uuid import UUID
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.domain.proposal import ProposalStatus

class PlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    goal_id: UUID
    prompt: str

class PlannedTaskRead(BaseModel):
    title: str
    notes: str | None = None
    estimated_minutes: int | None = None
    due_date: str | None = None
    priority: str

class ProposalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: str
    goal_id: UUID
    status: ProposalStatus
    proposal: dict[str, Any]
    created_at: datetime
