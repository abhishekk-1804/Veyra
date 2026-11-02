from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.domain.replanning import ReplanTrigger


class ReplanAdjustmentRead(BaseModel):
    task_id: UUID
    trigger: ReplanTrigger
    action: str
    reason: str
    suggested_priority: str | None = None


class ReplanProposalRead(BaseModel):
    goal_id: UUID
    summary: str
    adjustments: list[ReplanAdjustmentRead]


class ReplanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_time: datetime | None = None
    available_minutes: int = 120


class ReplanApplyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    task_id: UUID
    action: str
