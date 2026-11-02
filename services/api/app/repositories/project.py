from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project


class ProjectRepository:
    """Persistence access for Projects, scoped to a user."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, project: Project) -> Project:
        self._session.add(project)
        self._session.flush()
        return project

    def get(self, user_id: str, project_id: UUID) -> Project | None:
        stmt = select(Project).where(
            Project.id == project_id, Project.user_id == user_id
        )
        return self._session.scalar(stmt)

    def list(self, user_id: str, goal_id: UUID | None = None) -> list[Project]:
        stmt = select(Project).where(Project.user_id == user_id)
        if goal_id is not None:
            stmt = stmt.where(Project.goal_id == goal_id)
        stmt = stmt.order_by(Project.created_at.desc(), Project.id.asc())
        return list(self._session.scalars(stmt).all())