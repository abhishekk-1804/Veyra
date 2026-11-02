from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.dev_user import get_current_user_id
from app.db.session import get_db
from app.scheduling.scheduler import ExecutionPlan, ExecutionWindow, generate_schedule
from app.schemas.replanning import ReplanApplyRequest, ReplanProposalRead, ReplanRequest
from app.schemas.task import TaskRead
from app.services.replanner import ReplanningService
from app.services.task import TaskService

scheduling_router = APIRouter(prefix="/goals", tags=["scheduling", "replanning"])


class ScheduleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start_time: datetime
    available_minutes: int


@scheduling_router.post("/{goal_id}/schedule", response_model=ExecutionPlan)
def schedule_tasks(
    goal_id: UUID,
    request: ScheduleRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = TaskService(db)
    tasks = service.list(user_id, goal_id)

    tasks_dict = []
    for t in tasks:
        tasks_dict.append({
            "id": t.id,
            "title": t.title,
            "status": t.status,
            "priority": t.priority,
            "estimated_minutes": t.estimated_minutes,
            "due_date": t.due_date,
            "created_at": t.created_at,
        })

    window = ExecutionWindow(start_time=request.start_time, available_minutes=request.available_minutes)
    current_time = datetime.now(timezone.utc)

    plan = generate_schedule(tasks_dict, window, current_time)
    return plan


@scheduling_router.post("/{goal_id}/replan", response_model=ReplanProposalRead)
def propose_replan(
    goal_id: UUID,
    request: ReplanRequest = ReplanRequest(),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    replanner = ReplanningService(db)
    proposal = replanner.analyze_and_propose(
        user_id=user_id,
        goal_id=goal_id,
        current_time=request.current_time,
        available_minutes=request.available_minutes,
    )
    return proposal


@scheduling_router.post("/{goal_id}/replan/apply", response_model=TaskRead)
def apply_replan(
    goal_id: UUID,
    request: ReplanApplyRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    replanner = ReplanningService(db)
    task = replanner.apply_adjustment(
        user_id=user_id,
        goal_id=goal_id,
        task_id=request.task_id,
        action=request.action,
    )
    db.commit()
    db.refresh(task)
    return TaskRead.model_validate(task)
