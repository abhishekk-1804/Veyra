"""Project domain: enums and deterministic validation rules.

This module holds the business rules for a Project and is intentionally free of
any web/UI, AI, or persistence dependency.
"""

from datetime import date
from enum import StrEnum

MAX_TITLE_LENGTH = 120


class ProjectStatus(StrEnum):
    PLANNING = "PLANNING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"

    @classmethod
    def default(cls) -> "ProjectStatus":
        return cls.PLANNING


class ProjectPriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    @classmethod
    def default(cls) -> "ProjectPriority":
        return cls.MEDIUM


def is_valid_title(title: str) -> bool:
    """A title is valid when it is non-blank and within the max length."""
    return bool(title.strip()) and len(title) <= MAX_TITLE_LENGTH


def is_valid_date_range(start_date: date | None, target_date: date | None) -> bool:
    """Reject an obvious invalid combination: target before start."""
    if start_date is not None and target_date is not None and target_date < start_date:
        return False
    return True