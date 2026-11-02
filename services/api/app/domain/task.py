"""Task domain: enums and deterministic validation rules."""

from enum import StrEnum

MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 2000
MAX_ESTIMATED_MINUTES = 1440

class TaskStatus(StrEnum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

    @classmethod
    def default(cls) -> "TaskStatus":
        return cls.TODO

class TaskPriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"

    @classmethod
    def default(cls) -> "TaskPriority":
        return cls.MEDIUM

VALID_TRANSITIONS = {
    TaskStatus.TODO: {TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED, TaskStatus.CANCELLED},
    TaskStatus.IN_PROGRESS: {TaskStatus.COMPLETED, TaskStatus.TODO, TaskStatus.CANCELLED},
    TaskStatus.COMPLETED: set(),
    TaskStatus.CANCELLED: set(),
}

def is_valid_title(title: str) -> bool:
    return bool(title.strip()) and len(title.strip()) <= MAX_TITLE_LENGTH

def is_valid_description(description: str | None) -> bool:
    if description is None:
        return True
    return len(description) <= MAX_DESCRIPTION_LENGTH

def is_valid_estimate(estimate: int | None) -> bool:
    if estimate is None:
        return True
    return 0 < estimate <= MAX_ESTIMATED_MINUTES

def is_valid_transition(from_status: TaskStatus, to_status: TaskStatus) -> bool:
    if from_status == to_status:
        return True
    return to_status in VALID_TRANSITIONS.get(from_status, set())