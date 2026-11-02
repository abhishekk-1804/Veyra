from typing import Protocol
from pydantic import BaseModel

class PlannedTask(BaseModel):
    title: str
    notes: str | None = None
    estimated_minutes: int | None = None
    due_date: str | None = None
    priority: str

class PlanProposal(BaseModel):
    goal_id: str
    summary: str
    tasks: list[PlannedTask]

class AIProvider(Protocol):
    def generate_plan(self, goal_title: str, goal_description: str | None, prompt: str) -> PlanProposal:
        ...
