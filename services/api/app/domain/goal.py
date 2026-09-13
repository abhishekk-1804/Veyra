"""Goal domain: enums and deterministic validation rules.

This module holds the business rules for a Goal and is intentionally free of
any web/UI, AI, or persistence dependency. The API layer applies these rules
to input before anything reaches the database.
"""

from enum import StrEnum

MAX_TITLE_LENGTH = 120


class GoalStatus(StrEnum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"

    @classmethod
    def default(cls) -> "GoalStatus":
        return cls.ACTIVE


class GoalPriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    @classmethod
    def default(cls) -> "GoalPriority":
        return cls.MEDIUM


def is_valid_title(title: str) -> bool:
    """A title is valid when it is non-blank and within the max length."""
    return bool(title.strip()) and len(title) <= MAX_TITLE_LENGTH