from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ReplanTrigger(StrEnum):
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"
    DEFERRED = "DEFERRED"


@dataclass
class ReplanAdjustment:
    task_id: UUID
    trigger: ReplanTrigger
    action: str
    reason: str
    suggested_priority: str | None = None


@dataclass
class ReplanProposal:
    goal_id: UUID
    summary: str
    adjustments: list[ReplanAdjustment]
