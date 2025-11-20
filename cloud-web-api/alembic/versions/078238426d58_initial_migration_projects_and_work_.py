"""Initial migration - projects and work plan stages

Revision ID: 078238426d58
Revises: 
Create Date: 2025-10-20 22:43:17.930074

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '078238426d58'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_name', sa.String(), nullable=False),
        sa.Column('project_description', sa.String(), nullable=True),
        sa.Column('project_category', sa.String(), nullable=True),
        sa.Column('requesting_organization', sa.String(), nullable=True),
        sa.Column('contact_email', sa.String(), nullable=True),
        sa.Column('contact_phone', sa.String(), nullable=True),
        sa.Column('estimated_budget', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('priority_level', sa.String(), nullable=True),
        sa.Column('supporting_docs_url', sa.String(), nullable=True),
        sa.Column('submission_timestamp', sa.DateTime(), nullable=True),
        sa.Column('initiator_user_id', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_id'), 'projects', ['id'], unique=False)

    # Create work_plan_stages table
    op.create_table(
        'work_plan_stages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('stage_name', sa.String(), nullable=False),
        sa.Column('stage_start', sa.Date(), nullable=True),
        sa.Column('stage_end', sa.Date(), nullable=True),
        sa.Column('support_type', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('estimated_amount', sa.Float(), nullable=True),
        sa.Column('amount_currency', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('work_plan_stages')
    op.drop_index(op.f('ix_projects_id'), table_name='projects')
    op.drop_table('projects')
