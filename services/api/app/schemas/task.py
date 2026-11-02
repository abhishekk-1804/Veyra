from datetime import datetime
from uuid import UUID
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.task import (
    MAX_TITLE_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MAX_ESTIMATED_MINUTES,
    TaskPriority,
    TaskStatus,
    is_valid_description,
    is_valid_estimate,
    is_valid_title,
    is_valid_transition,
)

class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal_id: UUID
    title: str
    description: str | None = None
    status: TaskStatus = TaskStatus.default()
    priority: TaskPriority = TaskPriority.default()
    estimated_minutes: int | None = Field(default=None, gt=0, le=MAX_ESTIMATED_MINUTES)
    due_date: datetime | None = None

    @field_validator("title")
    @classmethod
    def _validate_title(cls, value: str) -> str:
        if not is_valid_title(value):
            raise ValueError(f"title must be non-blank and at most {MAX_TITLE_LENGTH} characters")
        return value.strip()

    @field_validator("description")
    @classmethod
    def _validate_description(cls, value: str | None) -> str | None:
        if not is_valid_description(value):
            raise ValueError(f"description must be at most {MAX_DESCRIPTION_LENGTH} characters")
        return value

class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    estimated_minutes: int | None = Field(default=None, gt=0, le=MAX_ESTIMATED_MINUTES)
    due_date: datetime | None = None

    @field_validator("title")
    @classmethod
    def _validate_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not is_valid_title(value):
            raise ValueError(f"title must be non-blank and at most {MAX_TITLE_LENGTH} characters")
        return value.strip()

    @field_validator("description")
    @classmethod
    def _validate_description(cls, value: str | None) -> str | None:
        if not is_valid_description(value):
            raise ValueError(f"description must be at most {MAX_DESCRIPTION_LENGTH} characters")
        return value
        
    @model_validator(mode="before")
    @classmethod
    def _validate_status_transition(cls, data: Any) -> Any:
        return data

class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: str
    goal_id: UUID
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    estimated_minutes: int | None
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime