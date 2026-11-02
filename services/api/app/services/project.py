from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.project import is_valid_date_range
from app.models.project import Project
from app.repositories.goal import GoalRepository
from app.repositories.project import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    """Application logic for Projects. Enforces ownership and references."""

    def __init__(self, session: Session) -> None:
        self._repo = ProjectRepository(session)
        self._session = session

    def create(self, user_id: str, data: ProjectCreate) -> Project:
        if data.goal_id is not None and not self._goal_owned(user_id, data.goal_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found"
            )
        project = Project(
            user_id=user_id,
            goal_id=data.goal_id,
            title=data.title,
            description=data.description,
            status=data.status,
            priority=data.priority,
            start_date=data.start_date,
            target_date=data.target_date,
        )
        self._repo.add(project)
        return project

    def list(self, user_id: str, goal_id: UUID | None = None) -> list[Project]:
        return self._repo.list(user_id, goal_id=goal_id)

    def get(self, user_id: str, project_id: UUID) -> Project | None:
        return self._repo.get(user_id, project_id)

    def update(
        self, user_id: str, project_id: UUID, data: ProjectUpdate
    ) -> Project | None:
        project = self._repo.get(user_id, project_id)
        if project is None:
            return None
        changes = data.model_dump(exclude_unset=True)

        if "goal_id" in changes and changes["goal_id"] is not None:
            if not self._goal_owned(user_id, changes["goal_id"]):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found"
                )

        merged_start = changes.get("start_date", project.start_date)
        merged_target = changes.get("target_date", project.target_date)
        if not is_valid_date_range(merged_start, merged_target):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="target_date cannot be before start_date",
            )

        for field, value in changes.items():
            setattr(project, field, value)
        self._session.flush()
        return project

    def _goal_owned(self, user_id: str, goal_id: UUID) -> bool:
        return GoalRepository(self._session).get(user_id, goal_id) is not None