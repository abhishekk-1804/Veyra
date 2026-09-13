from uuid import UUID

from sqlalchemy.orm import Session

from app.models.goal import Goal
from app.repositories.goal import GoalRepository
from app.schemas.goal import GoalCreate, GoalUpdate


class GoalService:
    """Application logic for Goals. Enforces ownership and applies updates."""

    def __init__(self, session: Session) -> None:
        self._repo = GoalRepository(session)
        self._session = session

    def create(self, user_id: str, data: GoalCreate) -> Goal:
        goal = Goal(
            user_id=user_id,
            title=data.title,
            description=data.description,
            status=data.status,
            priority=data.priority,
            target_date=data.target_date,
        )
        self._repo.add(goal)
        return goal

    def list(self, user_id: str) -> list[Goal]:
        return self._repo.list(user_id)

    def get(self, user_id: str, goal_id: UUID) -> Goal | None:
        return self._repo.get(user_id, goal_id)

    def update(self, user_id: str, goal_id: UUID, data: GoalUpdate) -> Goal | None:
        goal = self._repo.get(user_id, goal_id)
        if goal is None:
            return None
        changes = data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(goal, field, value)
        self._session.flush()
        return goal