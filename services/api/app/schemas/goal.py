from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.goal import GoalPriority, GoalStatus, MAX_TITLE_LENGTH, is_valid_title


class GoalCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: str | None = None
    status: GoalStatus = GoalStatus.default()
    priority: GoalPriority = GoalPriority.default()
    target_date: date | None = None

    @field_validator("title")
    @classmethod
    def _validate_title(cls, value: str) -> str:
        if not is_valid_title(value):
            raise ValueError(
                f"title must be non-blank and at most {MAX_TITLE_LENGTH} characters"
            )
        return value.strip()


class GoalUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    description: str | None = None
    status: GoalStatus | None = None
    priority: GoalPriority | None = None
    target_date: date | None = None

    @field_validator("title")
    @classmethod
    def _validate_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not is_valid_title(value):
            raise ValueError(
                f"title must be non-blank and at most {MAX_TITLE_LENGTH} characters"
            )
        return value.strip()


class GoalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: str
    title: str
    description: str | None
    status: GoalStatus
    priority: GoalPriority
    target_date: date | None
    created_at: datetime
    updated_at: datetime