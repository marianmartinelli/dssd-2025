"""add external_ref to project models

Revision ID: a9c2e1d4f5b6
Revises: f41ffd43acbb
Create Date: 2025-11-27 15:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9c2e1d4f5b6'
down_revision: Union[str, Sequence[str], None] = 'f41ffd43acbb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add external_ref to project models (nullable, no backfill)."""
    # Add nullable columns
    op.add_column('projects', sa.Column('external_ref', sa.String(length=36), nullable=True))
    op.add_column('work_plan_stages', sa.Column('external_ref', sa.String(length=36), nullable=True))
    op.add_column('collaboration_requests', sa.Column('external_ref', sa.String(length=36), nullable=True))
    op.add_column('observations', sa.Column('external_ref', sa.String(length=36), nullable=True))

    # Create unique constraints (allows NULL, but no duplicates for non-NULL values)
    op.create_unique_constraint('uq_projects_external_ref', 'projects', ['external_ref'])
    op.create_unique_constraint('uq_work_plan_stages_external_ref', 'work_plan_stages', ['external_ref'])
    op.create_unique_constraint('uq_collaboration_requests_external_ref', 'collaboration_requests', ['external_ref'])
    op.create_unique_constraint('uq_observations_external_ref', 'observations', ['external_ref'])

    # Create indexes for performance
    op.create_index(op.f('ix_projects_external_ref'), 'projects', ['external_ref'], unique=False)
    op.create_index(op.f('ix_work_plan_stages_external_ref'), 'work_plan_stages', ['external_ref'], unique=False)
    op.create_index(op.f('ix_collaboration_requests_external_ref'), 'collaboration_requests', ['external_ref'], unique=False)
    op.create_index(op.f('ix_observations_external_ref'), 'observations', ['external_ref'], unique=False)


def downgrade() -> None:
    """Remove external_ref columns."""
    # Drop indexes
    op.drop_index(op.f('ix_observations_external_ref'), table_name='observations')
    op.drop_index(op.f('ix_collaboration_requests_external_ref'), table_name='collaboration_requests')
    op.drop_index(op.f('ix_work_plan_stages_external_ref'), table_name='work_plan_stages')
    op.drop_index(op.f('ix_projects_external_ref'), table_name='projects')

    # Drop unique constraints
    op.drop_constraint('uq_observations_external_ref', 'observations', type_='unique')
    op.drop_constraint('uq_collaboration_requests_external_ref', 'collaboration_requests', type_='unique')
    op.drop_constraint('uq_work_plan_stages_external_ref', 'work_plan_stages', type_='unique')
    op.drop_constraint('uq_projects_external_ref', 'projects', type_='unique')

    # Drop columns
    op.drop_column('observations', 'external_ref')
    op.drop_column('collaboration_requests', 'external_ref')
    op.drop_column('work_plan_stages', 'external_ref')
    op.drop_column('projects', 'external_ref')
