from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.goal import Goal


class GoalRepository:
    """Persistence access for Goals, scoped to a user."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, goal: Goal) -> Goal:
        self._session.add(goal)
        self._session.flush()
        return goal

    def get(self, user_id: str, goal_id: UUID) -> Goal | None:
        stmt = select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
        return self._session.scalar(stmt)

    def list(self, user_id: str) -> list[Goal]:
        stmt = (
            select(Goal)
            .where(Goal.user_id == user_id)
            .order_by(Goal.created_at.desc(), Goal.id.asc())
        )
        return list(self._session.scalars(stmt).all())