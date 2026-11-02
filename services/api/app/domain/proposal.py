"""Proposal domain: enums."""

from enum import StrEnum

class ProposalStatus(StrEnum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"

    @classmethod
    def default(cls) -> "ProposalStatus":
        return cls.PENDING
