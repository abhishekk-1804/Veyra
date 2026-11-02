from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dev_user import get_current_user_id
from app.schemas.goal import GoalCreate, GoalRead, GoalUpdate
from app.services.goal import GoalService

router = APIRouter(prefix="/goals", tags=["goals"])


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found"
    )


@router.post("", response_model=GoalRead, status_code=status.HTTP_201_CREATED)
def create_goal(
    data: GoalCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> GoalRead:
    goal = GoalService(db).create(user_id, data)
    db.commit()
    db.refresh(goal)
    return GoalRead.model_validate(goal)


@router.get("", response_model=list[GoalRead])
def list_goals(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> list[GoalRead]:
    goals = GoalService(db).list(user_id)
    return [GoalRead.model_validate(g) for g in goals]


@router.get("/{goal_id}", response_model=GoalRead)
def get_goal(
    goal_id: UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> GoalRead:
    goal = GoalService(db).get(user_id, goal_id)
    if goal is None:
        raise _not_found()
    return GoalRead.model_validate(goal)


@router.patch("/{goal_id}", response_model=GoalRead)
def update_goal(
    goal_id: UUID,
    data: GoalUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> GoalRead:
    goal = GoalService(db).update(user_id, goal_id, data)
    if goal is None:
        raise _not_found()
    db.commit()
    db.refresh(goal)
    return GoalRead.model_validate(goal)


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> None:
    deleted = GoalService(db).delete(user_id, goal_id)
    if not deleted:
        raise _not_found()
    db.commit()