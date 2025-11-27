"""add external_ref to project models

Revision ID: 8908b1fa2d9a
Revises: d72168c3e854
Create Date: 2025-11-27 15:01:00.863610

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision: str = '8908b1fa2d9a'
down_revision: Union[str, Sequence[str], None] = 'd72168c3e854'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Step 1: Add nullable columns
    op.add_column('projects', sa.Column('external_ref', sa.String(length=36), nullable=True))
    op.add_column('work_plan_stages', sa.Column('external_ref', sa.String(length=36), nullable=True))
    op.add_column('collaboration_requests', sa.Column('external_ref', sa.String(length=36), nullable=True))
    op.add_column('observations', sa.Column('external_ref', sa.String(length=36), nullable=True))

    # Step 2: Backfill existing records with UUIDs
    connection = op.get_bind()

    # Backfill projects
    projects = connection.execute(sa.text("SELECT id FROM projects WHERE external_ref IS NULL")).fetchall()
    for project in projects:
        connection.execute(
            sa.text("UPDATE projects SET external_ref = :uuid WHERE id = :id"),
            {"uuid": str(uuid.uuid4()), "id": project[0]}
        )

    # Backfill work_plan_stages
    stages = connection.execute(sa.text("SELECT id FROM work_plan_stages WHERE external_ref IS NULL")).fetchall()
    for stage in stages:
        connection.execute(
            sa.text("UPDATE work_plan_stages SET external_ref = :uuid WHERE id = :id"),
            {"uuid": str(uuid.uuid4()), "id": stage[0]}
        )

    # Backfill collaboration_requests
    collabs = connection.execute(sa.text("SELECT id FROM collaboration_requests WHERE external_ref IS NULL")).fetchall()
    for collab in collabs:
        connection.execute(
            sa.text("UPDATE collaboration_requests SET external_ref = :uuid WHERE id = :id"),
            {"uuid": str(uuid.uuid4()), "id": collab[0]}
        )

    # Backfill observations
    observations = connection.execute(sa.text("SELECT id FROM observations WHERE external_ref IS NULL")).fetchall()
    for obs in observations:
        connection.execute(
            sa.text("UPDATE observations SET external_ref = :uuid WHERE id = :id"),
            {"uuid": str(uuid.uuid4()), "id": obs[0]}
        )

    # Step 3: Make columns NOT NULL
    op.alter_column('projects', 'external_ref', nullable=False)
    op.alter_column('work_plan_stages', 'external_ref', nullable=False)
    op.alter_column('collaboration_requests', 'external_ref', nullable=False)
    op.alter_column('observations', 'external_ref', nullable=False)

    # Step 4: Create unique constraints
    op.create_unique_constraint('uq_projects_external_ref', 'projects', ['external_ref'])
    op.create_unique_constraint('uq_work_plan_stages_external_ref', 'work_plan_stages', ['external_ref'])
    op.create_unique_constraint('uq_collaboration_requests_external_ref', 'collaboration_requests', ['external_ref'])
    op.create_unique_constraint('uq_observations_external_ref', 'observations', ['external_ref'])

    # Step 5: Create indexes for performance
    op.create_index(op.f('ix_projects_external_ref'), 'projects', ['external_ref'], unique=False)
    op.create_index(op.f('ix_work_plan_stages_external_ref'), 'work_plan_stages', ['external_ref'], unique=False)
    op.create_index(op.f('ix_collaboration_requests_external_ref'), 'collaboration_requests', ['external_ref'], unique=False)
    op.create_index(op.f('ix_observations_external_ref'), 'observations', ['external_ref'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
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
