from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.domain.project import (
    MAX_TITLE_LENGTH,
    ProjectPriority,
    ProjectStatus,
    is_valid_date_range,
    is_valid_title,
)


def _validate_title(value: str) -> str:
    if not is_valid_title(value):
        raise ValueError(
            f"title must be non-blank and at most {MAX_TITLE_LENGTH} characters"
        )
    return value.strip()


def _validate_date_range(
    start_date: date | None, target_date: date | None
) -> None:
    if not is_valid_date_range(start_date, target_date):
        raise ValueError("target_date cannot be before start_date")


class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: str | None = None
    goal_id: UUID | None = None
    status: ProjectStatus = ProjectStatus.default()
    priority: ProjectPriority = ProjectPriority.default()
    start_date: date | None = None
    target_date: date | None = None

    @field_validator("title")
    @classmethod
    def _validate_title_field(cls, value: str) -> str:
        return _validate_title(value)

    @model_validator(mode="after")
    def _validate_dates(self) -> "ProjectCreate":
        _validate_date_range(self.start_date, self.target_date)
        return self


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    description: str | None = None
    goal_id: UUID | None = None
    status: ProjectStatus | None = None
    priority: ProjectPriority | None = None
    start_date: date | None = None
    target_date: date | None = None

    @field_validator("title")
    @classmethod
    def _validate_title_field(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_title(value)

    @model_validator(mode="after")
    def _validate_dates(self) -> "ProjectUpdate":
        _validate_date_range(self.start_date, self.target_date)
        return self


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: str
    goal_id: UUID | None
    title: str
    description: str | None
    status: ProjectStatus
    priority: ProjectPriority
    start_date: date | None
    target_date: date | None
    created_at: datetime
    updated_at: datetime