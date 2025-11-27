"""change_default_project_status_to_requesting_support

Revision ID: a1b2c3d4e5f6
Revises: f41ffd43acbb
Create Date: 2025-11-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'cad15b88db24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - change default project status to requesting_support."""
    # Change the default value for the status column
    op.alter_column('projects', 'status',
                   existing_type=sa.String(),
                   server_default='requesting_support',
                   existing_nullable=False)


def downgrade() -> None:
    """Downgrade schema - revert default project status to in_progress."""
    # Revert to the old default
    op.alter_column('projects', 'status',
                   existing_type=sa.String(),
                   server_default='in_progress',
                   existing_nullable=False)
