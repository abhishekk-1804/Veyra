from datetime import datetime, timezone
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domain.replanning import ReplanAdjustment, ReplanProposal, ReplanTrigger
from app.domain.task import TaskPriority, TaskStatus
from app.models.task import Task
from app.repositories.goal import GoalRepository
from app.repositories.task import TaskRepository
from app.scheduling.scheduler import ExecutionWindow, generate_schedule


class ReplanningService:
    """Application service for generating and applying reviewable replanning adjustments."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._goal_repo = GoalRepository(session)
        self._task_repo = TaskRepository(session)

    def analyze_and_propose(
        self,
        user_id: str,
        goal_id: UUID,
        current_time: datetime | None = None,
        available_minutes: int = 120,
    ) -> ReplanProposal:
        """Analyzes execution bottlenecks and generates a proposal. NEVER mutates state."""
        goal = self._goal_repo.get(user_id, goal_id)
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")

        tasks = self._task_repo.list(user_id, goal_id)
        now = current_time or datetime.now(timezone.utc)
        adjustments: list[ReplanAdjustment] = []

        # 1. Overdue detection
        for t in tasks:
            if t.status in (TaskStatus.TODO, TaskStatus.IN_PROGRESS):
                if t.due_date is not None:
                    # Normalize comparison to UTC
                    due = t.due_date if t.due_date.tzinfo else t.due_date.replace(tzinfo=timezone.utc)
                    curr = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
                    if due < curr:
                        adjustments.append(
                            ReplanAdjustment(
                                task_id=t.id,
                                trigger=ReplanTrigger.OVERDUE,
                                action="ESCALATE_PRIORITY",
                                reason=f"Task was due at {t.due_date.isoformat()} and is now overdue",
                                suggested_priority=TaskPriority.URGENT,
                            )
                        )

        # 2. Cancelled task handling
        for t in tasks:
            if t.status == TaskStatus.CANCELLED:
                adjustments.append(
                    ReplanAdjustment(
                        task_id=t.id,
                        trigger=ReplanTrigger.CANCELLED,
                        action="ARCHIVE_OR_REOPEN",
                        reason="Task was marked cancelled; consider removing or reactivating if dependencies exist",
                    )
                )

        # 3. Deferred task handling from deterministic scheduling
        tasks_dict = [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status,
                "priority": t.priority,
                "estimated_minutes": t.estimated_minutes,
                "due_date": t.due_date,
                "created_at": t.created_at,
            }
            for t in tasks
        ]
        window = ExecutionWindow(start_time=now, available_minutes=available_minutes)
        plan = generate_schedule(tasks_dict, window, now)

        for d in plan.deferred:
            if d.status in (TaskStatus.TODO, TaskStatus.IN_PROGRESS):
                # Ensure we don't duplicate if already flagged as overdue
                if not any(a.task_id == UUID(d.task_id) for a in adjustments):
                    adjustments.append(
                        ReplanAdjustment(
                            task_id=UUID(d.task_id),
                            trigger=ReplanTrigger.DEFERRED,
                            action="RESCHEDULE_NEXT_WINDOW",
                            reason=f"Exceeded available capacity window of {available_minutes}m",
                        )
                    )

        summary = (
            f"Replanning analysis for goal {goal.title}: {len(adjustments)} adjustment(s) proposed. "
            f"No changes applied automatically."
        )

        return ReplanProposal(
            goal_id=goal_id,
            summary=summary,
            adjustments=adjustments,
        )

    def apply_adjustment(
        self,
        user_id: str,
        goal_id: UUID,
        task_id: UUID,
        action: str,
    ) -> Task:
        """Applies an approved adjustment. Enforces ownership."""
        goal = self._goal_repo.get(user_id, goal_id)
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")

        task = self._task_repo.get(user_id, task_id)
        if not task or task.goal_id != goal_id:
            raise HTTPException(status_code=404, detail="Task not found")

        if action == "ESCALATE_PRIORITY":
            task.priority = TaskPriority.URGENT
        elif action == "RESET_STATUS":
            task.status = TaskStatus.TODO

        self._session.flush()
        return task
