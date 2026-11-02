"""add tasks and proposals

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0002_add_tasks_and_proposals"
down_revision: Union[str, None] = "0001_create_goals"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # create enums
    sa.Enum('TODO', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', name='task_status').create(op.get_bind())
    sa.Enum('LOW', 'MEDIUM', 'HIGH', 'URGENT', name='task_priority').create(op.get_bind())
    sa.Enum('PENDING', 'ACCEPTED', 'REJECTED', name='proposal_status').create(op.get_bind())

    # create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.String(length=64), nullable=False),
        sa.Column('goal_id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('TODO', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', name='task_status'), nullable=False),
        sa.Column('priority', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'URGENT', name='task_priority'), nullable=False),
        sa.Column('estimated_minutes', sa.Integer(), nullable=True),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_user_id'), 'tasks', ['user_id'], unique=False)
    op.create_index(op.f('ix_tasks_goal_id'), 'tasks', ['goal_id'], unique=False)

    # create proposals table
    op.create_table(
        'plan_proposals',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.String(length=64), nullable=False),
        sa.Column('goal_id', sa.Uuid(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'ACCEPTED', 'REJECTED', name='proposal_status'), nullable=False),
        sa.Column('proposal_payload', sa.Text(), nullable=False),
        sa.Column('fingerprint', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_proposals_user_id'), 'plan_proposals', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_plan_proposals_user_id'), table_name='plan_proposals')
    op.drop_table('plan_proposals')
    
    op.drop_index(op.f('ix_tasks_goal_id'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_user_id'), table_name='tasks')
    op.drop_table('tasks')

    sa.Enum(name='proposal_status').drop(op.get_bind())
    sa.Enum(name='task_priority').drop(op.get_bind())
    sa.Enum(name='task_status').drop(op.get_bind())
