"""create goals table

Revision ID: 0001_create_goals
Revises:
Create Date: 2026-01-01 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_create_goals"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _uuid() -> sa.Uuid:
    return sa.Uuid()


def upgrade() -> None:
    goal_status = sa.Enum(
        "ACTIVE", "COMPLETED", "PAUSED", "ARCHIVED", name="goal_status"
    )
    goal_priority = sa.Enum(
        "LOW", "MEDIUM", "HIGH", "CRITICAL", name="goal_priority"
    )

    op.create_table(
        "goals",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", goal_status, nullable=False),
        sa.Column("priority", goal_priority, nullable=False),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index(op.f("ix_goals_user_id"), "goals", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_goals_user_id"), table_name="goals")
    op.drop_table("goals")
    sa.Enum(name="goal_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="goal_priority").drop(op.get_bind(), checkfirst=True)