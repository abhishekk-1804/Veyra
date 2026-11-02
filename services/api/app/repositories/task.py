from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.task import Task

class TaskRepository:
    """Persistence access for Tasks, scoped to a user."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, task: Task) -> Task:
        self._session.add(task)
        self._session.flush()
        return task

    def add_all(self, tasks: list[Task]) -> list[Task]:
        self._session.add_all(tasks)
        self._session.flush()
        return tasks

    def get(self, user_id: str, task_id: UUID) -> Task | None:
        stmt = select(Task).where(Task.id == task_id, Task.user_id == user_id)
        return self._session.scalar(stmt)

    def list(self, user_id: str, goal_id: UUID | None = None) -> list[Task]:
        stmt = select(Task).where(Task.user_id == user_id)
        if goal_id is not None:
            stmt = stmt.where(Task.goal_id == goal_id)
        stmt = stmt.order_by(Task.created_at.desc(), Task.id.asc())
        return list(self._session.scalars(stmt).all())

    def delete(self, user_id: str, task_id: UUID) -> bool:
        task = self.get(user_id, task_id)
        if task is None:
            return False
        self._session.delete(task)
        self._session.flush()
        return True