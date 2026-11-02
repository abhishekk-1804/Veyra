import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.ai.dev_provider import DevAIProvider
from app.dev_user import get_current_user_id
from app.db.session import get_db
from app.schemas.proposal import PlanRequest, ProposalRead
from app.schemas.task import TaskRead
from app.services.ai_planner import AIPlannerService

ai_router = APIRouter(prefix="/ai", tags=["ai"])

def get_ai_provider():
    return DevAIProvider()

@ai_router.post("/plans", response_model=ProposalRead, status_code=status.HTTP_201_CREATED)
def generate_plan(
    request: PlanRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    provider = Depends(get_ai_provider),
):
    service = AIPlannerService(db, provider)
    proposal = service.generate_plan(user_id, request.goal_id, request.prompt)
    db.commit()
    db.refresh(proposal)
    return ProposalRead(
        id=proposal.id,
        user_id=proposal.user_id,
        goal_id=proposal.goal_id,
        status=proposal.status,
        proposal=json.loads(proposal.proposal_payload),
        created_at=proposal.created_at,
    )

@ai_router.post("/plans/{proposal_id}/approve", response_model=list[TaskRead])
def approve_plan(
    proposal_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    provider = Depends(get_ai_provider),
):
    service = AIPlannerService(db, provider)
    tasks = service.approve_proposal(user_id, proposal_id)
    db.commit()
    return [TaskRead.model_validate(t) for t in tasks]

@ai_router.post("/plans/{proposal_id}/reject", status_code=status.HTTP_204_NO_CONTENT)
def reject_plan(
    proposal_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    provider = Depends(get_ai_provider),
):
    service = AIPlannerService(db, provider)
    service.reject_proposal(user_id, proposal_id)
    db.commit()
