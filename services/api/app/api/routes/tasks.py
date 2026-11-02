from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dev_user import get_current_user_id
from app.db.session import get_db
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services.task import TaskService

goals_router = APIRouter(prefix="/goals", tags=["goals-tasks"])
tasks_router = APIRouter(prefix="/tasks", tags=["tasks"])

@goals_router.post("/{goal_id}/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(
    goal_id: UUID,
    data: TaskCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    if data.goal_id != goal_id:
        raise HTTPException(status_code=422, detail="goal_id mismatch")
    service = TaskService(db)
    task = service.create(user_id, goal_id, data)
    db.commit()
    db.refresh(task)
    return TaskRead.model_validate(task)

@goals_router.get("/{goal_id}/tasks", response_model=list[TaskRead])
def list_tasks(
    goal_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = TaskService(db)
    tasks = service.list(user_id, goal_id)
    return [TaskRead.model_validate(t) for t in tasks]

@tasks_router.get("/{task_id}", response_model=TaskRead)
def get_task(
    task_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = TaskService(db)
    task = service.get(user_id, task_id)
    return TaskRead.model_validate(task)

@tasks_router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: UUID,
    data: TaskUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = TaskService(db)
    task = service.update(user_id, task_id, data)
    db.commit()
    db.refresh(task)
    return TaskRead.model_validate(task)

@tasks_router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = TaskService(db)
    service.delete(user_id, task_id)
    db.commit()
