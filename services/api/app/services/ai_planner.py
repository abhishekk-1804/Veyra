import hashlib
import json
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.ai.provider import AIProvider
from app.ai.validation import validate_proposal
from app.domain.proposal import ProposalStatus
from app.models.proposal import PlanProposal
from app.repositories.goal import GoalRepository
from app.repositories.proposal import ProposalRepository
from app.schemas.task import TaskCreate
from app.services.task import TaskService

class AIPlannerService:
    def __init__(self, session: Session, ai_provider: AIProvider) -> None:
        self._session = session
        self._goal_repo = GoalRepository(session)
        self._proposal_repo = ProposalRepository(session)
        self._task_service = TaskService(session)
        self._ai_provider = ai_provider

    def generate_plan(self, user_id: str, goal_id: UUID, prompt: str) -> PlanProposal:
        goal = self._goal_repo.get(user_id, goal_id)
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")

        raw_proposal = self._ai_provider.generate_plan(goal.title, goal.description, prompt)
        raw_proposal.goal_id = str(goal_id)
        
        try:
            validated_proposal = validate_proposal(raw_proposal)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

        payload_dict = validated_proposal.model_dump()
        payload_json = json.dumps(payload_dict, sort_keys=True)
        fingerprint = hashlib.sha256(payload_json.encode()).hexdigest()

        proposal = PlanProposal(
            user_id=user_id,
            goal_id=goal_id,
            status=ProposalStatus.PENDING,
            proposal_payload=payload_json,
            fingerprint=fingerprint,
        )
        self._proposal_repo.add(proposal)
        return proposal

    def approve_proposal(self, user_id: str, proposal_id: UUID) -> list:
        proposal = self._proposal_repo.get(user_id, proposal_id)
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
            
        if proposal.status == ProposalStatus.ACCEPTED:
            return []  # Idempotent: return empty list on duplicate approval

        if proposal.status == ProposalStatus.REJECTED:
            raise HTTPException(status_code=422, detail="Proposal already rejected")

        # 1. Anti-tampering check: verify fingerprint matches current stored payload
        computed_fingerprint = hashlib.sha256(proposal.proposal_payload.encode()).hexdigest()
        if proposal.fingerprint != computed_fingerprint:
            raise HTTPException(status_code=422, detail="Proposal payload has been tampered with")

        # 2. Re-validate payload structure and business constraints
        try:
            payload_data = json.loads(proposal.proposal_payload)
            from app.ai.provider import PlanProposal
            proposal_obj = PlanProposal.model_validate(payload_data)
            validate_proposal(proposal_obj)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Proposal validation failed: {e}")

        # 3. Build TaskCreate models with parsed dates
        tasks_to_create = []
        for t in proposal_obj.tasks:
            due_dt = None
            if t.due_date:
                from datetime import datetime
                due_dt = datetime.fromisoformat(t.due_date.replace("Z", "+00:00"))

            task_create = TaskCreate(
                goal_id=proposal.goal_id,
                title=t.title,
                description=t.notes,
                estimated_minutes=t.estimated_minutes,
                due_date=due_dt,
                priority=t.priority,
            )
            tasks_to_create.append(task_create)
            
        # 4. Atomic TaskService transaction
        created_tasks = self._task_service.create_many(user_id, proposal.goal_id, tasks_to_create)
        
        # 5. Transition proposal to ACCEPTED
        proposal.status = ProposalStatus.ACCEPTED
        self._session.flush()
        
        return created_tasks

    def reject_proposal(self, user_id: str, proposal_id: UUID) -> None:
        proposal = self._proposal_repo.get(user_id, proposal_id)
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
            
        if proposal.status == ProposalStatus.ACCEPTED:
            raise HTTPException(status_code=422, detail="Proposal already accepted")

        if proposal.status == ProposalStatus.PENDING:
            proposal.status = ProposalStatus.REJECTED
            self._session.flush()

