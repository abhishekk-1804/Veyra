from dataclasses import dataclass
from datetime import datetime
from typing import Any

@dataclass
class ExecutionWindow:
    start_time: datetime
    available_minutes: int

@dataclass
class ScheduledTask:
    task_id: str
    title: str
    status: str
    priority: str
    estimated_minutes: int
    due_date: datetime | None
    start_offset: int
    end_offset: int

@dataclass
class ExecutionPlan:
    scheduled: list[ScheduledTask]
    deferred: list[ScheduledTask]
    total_scheduled_minutes: int
    total_deferred_minutes: int

def _normalize_dt(dt: Any) -> float:
    if dt is None:
        return float("inf")
    if isinstance(dt, datetime):
        if dt.tzinfo is not None:
            return dt.timestamp()
        from datetime import timezone
        return dt.replace(tzinfo=timezone.utc).timestamp()
    return float("inf")

def _sort_key(t: dict) -> tuple:
    # 1. Active/incomplete before completed/cancelled (False before True)
    is_completed = t.get("status") in ("COMPLETED", "CANCELLED")
    
    # 2. IN_PROGRESS before TODO (False before True)
    is_todo = t.get("status") != "IN_PROGRESS"
    
    # 3. Earlier due date first
    # 4. No due date after dated tasks (False [has date] before True [no date])
    has_no_due_date = t.get("due_date") is None
    due_date_ts = _normalize_dt(t.get("due_date"))
    
    # 5. Higher priority first: URGENT (0) > HIGH (1) > MEDIUM (2) > LOW (3)
    priority_order = {"URGENT": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    priority_rank = priority_order.get(t.get("priority", "MEDIUM"), 2)
    
    # 6. Shorter estimated duration first
    estimate = t.get("estimated_minutes") if t.get("estimated_minutes") is not None else 9999
    
    # 7. Earlier created_at first
    created_at_ts = _normalize_dt(t.get("created_at")) if t.get("created_at") is not None else 0.0
    
    # 8. Stable task id as final deterministic tie-breaker
    task_id = str(t.get("id", ""))
    
    return (
        is_completed,
        is_todo,
        has_no_due_date,
        due_date_ts,
        priority_rank,
        estimate,
        created_at_ts,
        task_id,
    )

def generate_schedule(tasks: list[dict], window: ExecutionWindow, current_time: datetime) -> ExecutionPlan:
    """Pure deterministic scheduling function.
    
    Inputs:
        tasks: list of task dictionaries
        window: ExecutionWindow(start_time, available_minutes)
        current_time: datetime (explicit input, never reads system clock)
        
    Outputs:
        ExecutionPlan with scheduled and deferred tasks.
    """
    if window.available_minutes < 0:
        raise ValueError("available_minutes must be non-negative")
    if window.start_time is None:
        raise ValueError("start_time is required")

    sorted_tasks = sorted(tasks, key=_sort_key)
    
    scheduled = []
    deferred = []
    current_offset = 0
    total_scheduled = 0
    total_deferred = 0
    
    for t in sorted_tasks:
        est = t.get("estimated_minutes") or 30 # fallback for scheduling if None
        
        task_obj = ScheduledTask(
            task_id=str(t["id"]),
            title=t["title"],
            status=t["status"],
            priority=t["priority"],
            estimated_minutes=est,
            due_date=t.get("due_date"),
            start_offset=0,
            end_offset=0
        )
        
        if t.get("status") in ("COMPLETED", "CANCELLED"):
            task_obj.start_offset = current_offset
            task_obj.end_offset = current_offset
            deferred.append(task_obj)
            continue
            
        if current_offset + est <= window.available_minutes:
            task_obj.start_offset = current_offset
            task_obj.end_offset = current_offset + est
            scheduled.append(task_obj)
            current_offset += est
            total_scheduled += est
        else:
            task_obj.start_offset = current_offset
            task_obj.end_offset = current_offset + est
            deferred.append(task_obj)
            total_deferred += est
            
    return ExecutionPlan(
        scheduled=scheduled,
        deferred=deferred,
        total_scheduled_minutes=total_scheduled,
        total_deferred_minutes=total_deferred
    )
