from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domain.task import is_valid_transition
from app.models.task import Task
from app.repositories.goal import GoalRepository
from app.repositories.task import TaskRepository
from app.schemas.task import TaskCreate, TaskUpdate

class TaskService:
    def __init__(self, session: Session) -> None:
        self._repo = TaskRepository(session)
        self._goal_repo = GoalRepository(session)
        self._session = session

    def _verify_goal(self, user_id: str, goal_id: UUID) -> None:
        if not self._goal_repo.get(user_id, goal_id):
            raise HTTPException(status_code=404, detail="Goal not found")

    def create(self, user_id: str, goal_id: UUID, data: TaskCreate) -> Task:
        self._verify_goal(user_id, goal_id)
        task = Task(
            user_id=user_id,
            goal_id=goal_id,
            title=data.title,
            description=data.description,
            status=data.status,
            priority=data.priority,
            estimated_minutes=data.estimated_minutes,
            due_date=data.due_date,
        )
        self._repo.add(task)
        return task

    def create_many(self, user_id: str, goal_id: UUID, tasks: list[TaskCreate]) -> list[Task]:
        self._verify_goal(user_id, goal_id)
        task_models = [
            Task(
                user_id=user_id,
                goal_id=goal_id,
                title=t.title,
                description=t.description,
                status=t.status,
                priority=t.priority,
                estimated_minutes=t.estimated_minutes,
                due_date=t.due_date,
            )
            for t in tasks
        ]
        self._repo.add_all(task_models)
        return task_models

    def list(self, user_id: str, goal_id: UUID | None = None) -> list[Task]:
        if goal_id is not None:
            self._verify_goal(user_id, goal_id)
        return self._repo.list(user_id, goal_id)

    def get(self, user_id: str, task_id: UUID) -> Task | None:
        task = self._repo.get(user_id, task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

    def update(self, user_id: str, task_id: UUID, data: TaskUpdate) -> Task | None:
        task = self.get(user_id, task_id)
        changes = data.model_dump(exclude_unset=True)
        
        if "status" in changes:
            if not is_valid_transition(task.status, changes["status"]):
                raise HTTPException(status_code=422, detail="Invalid status transition")
        
        for field, value in changes.items():
            setattr(task, field, value)
        self._session.flush()
        return task

    def delete(self, user_id: str, task_id: UUID) -> bool:
        if not self._repo.delete(user_id, task_id):
            raise HTTPException(status_code=404, detail="Task not found")
        return True