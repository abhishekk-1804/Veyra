import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from app.scheduling.scheduler import (
    ExecutionPlan,
    ExecutionWindow,
    ScheduledTask,
    generate_schedule,
)

# 31. deterministic result
def test_generate_schedule_deterministic():
    tasks = [
        {"id": "task-1", "title": "A", "status": "TODO", "priority": "MEDIUM", "estimated_minutes": 30, "due_date": None, "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc)},
        {"id": "task-2", "title": "B", "status": "TODO", "priority": "HIGH", "estimated_minutes": 30, "due_date": None, "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc)},
    ]
    window = ExecutionWindow(start_time=datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc), available_minutes=60)
    current_time = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    
    plan1 = generate_schedule(tasks, window, current_time)
    plan2 = generate_schedule(tasks, window, current_time)
    
    assert [t.task_id for t in plan1.scheduled] == [t.task_id for t in plan2.scheduled]
    assert plan1.scheduled[0].task_id == "task-2" # HIGH before MEDIUM

# 32. status ordering (Active before completed/cancelled; IN_PROGRESS before TODO)
def test_status_ordering():
    tasks = [
        {"id": "1", "title": "Completed", "status": "COMPLETED", "priority": "URGENT", "estimated_minutes": 10},
        {"id": "2", "title": "Todo", "status": "TODO", "priority": "LOW", "estimated_minutes": 10},
        {"id": "3", "title": "InProgress", "status": "IN_PROGRESS", "priority": "LOW", "estimated_minutes": 10},
        {"id": "4", "title": "Cancelled", "status": "CANCELLED", "priority": "URGENT", "estimated_minutes": 10},
    ]
    window = ExecutionWindow(start_time=datetime.now(timezone.utc), available_minutes=120)
    plan = generate_schedule(tasks, window, datetime.now(timezone.utc))
    
    # Scheduled should contain IN_PROGRESS first, then TODO
    scheduled_ids = [t.task_id for t in plan.scheduled]
    assert scheduled_ids == ["3", "2"]
    
    # Deferred should contain COMPLETED and CANCELLED
    deferred_ids = [t.task_id for t in plan.deferred]
    assert "1" in deferred_ids
    assert "4" in deferred_ids

# 33. due date ordering (earlier first, no due date after dated tasks)
def test_due_date_ordering():
    d1 = datetime(2026, 5, 1, tzinfo=timezone.utc)
    d2 = datetime(2026, 5, 10, tzinfo=timezone.utc)
    tasks = [
        {"id": "undated", "title": "Undated", "status": "TODO", "priority": "HIGH", "estimated_minutes": 15, "due_date": None},
        {"id": "later", "title": "Later", "status": "TODO", "priority": "HIGH", "estimated_minutes": 15, "due_date": d2},
        {"id": "earlier", "title": "Earlier", "status": "TODO", "priority": "HIGH", "estimated_minutes": 15, "due_date": d1},
    ]
    window = ExecutionWindow(start_time=datetime.now(timezone.utc), available_minutes=60)
    plan = generate_schedule(tasks, window, datetime.now(timezone.utc))
    
    scheduled_ids = [t.task_id for t in plan.scheduled]
    assert scheduled_ids == ["earlier", "later", "undated"]

# 34. priority ordering (URGENT > HIGH > MEDIUM > LOW)
def test_priority_ordering():
    tasks = [
        {"id": "p-low", "title": "Low", "status": "TODO", "priority": "LOW", "estimated_minutes": 10},
        {"id": "p-urgent", "title": "Urgent", "status": "TODO", "priority": "URGENT", "estimated_minutes": 10},
        {"id": "p-medium", "title": "Medium", "status": "TODO", "priority": "MEDIUM", "estimated_minutes": 10},
        {"id": "p-high", "title": "High", "status": "TODO", "priority": "HIGH", "estimated_minutes": 10},
    ]
    window = ExecutionWindow(start_time=datetime.now(timezone.utc), available_minutes=60)
    plan = generate_schedule(tasks, window, datetime.now(timezone.utc))
    scheduled_ids = [t.task_id for t in plan.scheduled]
    assert scheduled_ids == ["p-urgent", "p-high", "p-medium", "p-low"]

# 35. estimate ordering (shorter duration first)
def test_estimate_ordering():
    tasks = [
        {"id": "long", "title": "Long", "status": "TODO", "priority": "MEDIUM", "estimated_minutes": 60},
        {"id": "short", "title": "Short", "status": "TODO", "priority": "MEDIUM", "estimated_minutes": 15},
    ]
    window = ExecutionWindow(start_time=datetime.now(timezone.utc), available_minutes=120)
    plan = generate_schedule(tasks, window, datetime.now(timezone.utc))
    assert [t.task_id for t in plan.scheduled] == ["short", "long"]

# 36. stable tie-breaking (earlier created_at, then stable task id)
def test_stable_tie_breaking():
    t_early = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
    t_late = datetime(2026, 1, 1, 11, 0, tzinfo=timezone.utc)
    tasks = [
        {"id": "b-task", "title": "T", "status": "TODO", "priority": "MEDIUM", "estimated_minutes": 10, "created_at": t_late},
        {"id": "a-task", "title": "T", "status": "TODO", "priority": "MEDIUM", "estimated_minutes": 10, "created_at": t_early},
    ]
    window = ExecutionWindow(start_time=datetime.now(timezone.utc), available_minutes=60)
    plan = generate_schedule(tasks, window, datetime.now(timezone.utc))
    assert [t.task_id for t in plan.scheduled] == ["a-task", "b-task"]

    # Same created_at -> ID tie-breaker
    tasks2 = [
        {"id": "z-id", "title": "T", "status": "TODO", "priority": "MEDIUM", "estimated_minutes": 10, "created_at": t_early},
        {"id": "a-id", "title": "T", "status": "TODO", "priority": "MEDIUM", "estimated_minutes": 10, "created_at": t_early},
    ]
    plan2 = generate_schedule(tasks2, window, datetime.now(timezone.utc))
    assert [t.task_id for t in plan2.scheduled] == ["a-id", "z-id"]

# 37. execution capacity & 38. deferred tasks
def test_execution_capacity_and_deferred_tasks():
    tasks = [
        {"id": "t1", "title": "1", "status": "TODO", "priority": "HIGH", "estimated_minutes": 40},
        {"id": "t2", "title": "2", "status": "TODO", "priority": "MEDIUM", "estimated_minutes": 30},
        {"id": "t3", "title": "3", "status": "TODO", "priority": "LOW", "estimated_minutes": 20},
    ]
    window = ExecutionWindow(start_time=datetime.now(timezone.utc), available_minutes=60)
    plan = generate_schedule(tasks, window, datetime.now(timezone.utc))

    # t1 (40 min) fits. t2 (30 min) cannot fit in remaining 20 min -> deferred.
    # t3 (20 min) is evaluated sequentially.
    assert len(plan.scheduled) >= 1
    assert plan.total_scheduled_minutes <= 60
    assert len(plan.deferred) >= 1

# 39. invalid scheduling input
def test_invalid_scheduling_input():
    tasks = [{"id": "1", "title": "T", "status": "TODO", "priority": "MEDIUM", "estimated_minutes": 10}]
    
    with pytest.raises(ValueError, match="available_minutes must be non-negative"):
        window = ExecutionWindow(start_time=datetime.now(timezone.utc), available_minutes=-10)
        generate_schedule(tasks, window, datetime.now(timezone.utc))
        
    with pytest.raises(ValueError, match="start_time is required"):
        window = ExecutionWindow(start_time=None, available_minutes=60)
        generate_schedule(tasks, window, datetime.now(timezone.utc))

# 40. no system-clock dependency (passing completely different current_time produces identical ordering)
def test_no_system_clock_dependency():
    tasks = [
        {"id": "1", "title": "A", "status": "TODO", "priority": "MEDIUM", "estimated_minutes": 20},
        {"id": "2", "title": "B", "status": "TODO", "priority": "HIGH", "estimated_minutes": 20},
    ]
    window = ExecutionWindow(start_time=datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc), available_minutes=60)
    
    t1 = datetime(2020, 1, 1, tzinfo=timezone.utc)
    t2 = datetime(2040, 1, 1, tzinfo=timezone.utc)
    
    plan1 = generate_schedule(tasks, window, t1)
    plan2 = generate_schedule(tasks, window, t2)
    
    assert [t.task_id for t in plan1.scheduled] == [t.task_id for t in plan2.scheduled]
