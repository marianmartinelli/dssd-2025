"""add is_completed to work_plan_stages

Revision ID: 2a6985fd3004
Revises: 059e81ee2cbb
Create Date: 2025-10-24 15:39:03.483576

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2a6985fd3004'
down_revision: Union[str, Sequence[str], None] = '059e81ee2cbb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add is_completed column to work_plan_stages table with default value False
    op.add_column('work_plan_stages', sa.Column('is_completed', sa.Boolean(), nullable=True, server_default='false'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove is_completed column from work_plan_stages table
    op.drop_column('work_plan_stages', 'is_completed')
