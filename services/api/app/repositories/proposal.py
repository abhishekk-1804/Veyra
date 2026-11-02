from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.proposal import PlanProposal

class ProposalRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, proposal: PlanProposal) -> PlanProposal:
        self._session.add(proposal)
        self._session.flush()
        return proposal

    def get(self, user_id: str, proposal_id: UUID) -> PlanProposal | None:
        stmt = select(PlanProposal).where(PlanProposal.id == proposal_id, PlanProposal.user_id == user_id)
        return self._session.scalar(stmt)
