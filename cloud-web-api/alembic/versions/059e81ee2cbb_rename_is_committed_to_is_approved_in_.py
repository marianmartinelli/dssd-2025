"""rename is_committed to is_approved in collaboration_requests

Revision ID: 059e81ee2cbb
Revises: 5ae701122239
Create Date: 2025-10-24 15:25:07.912119

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '059e81ee2cbb'
down_revision: Union[str, Sequence[str], None] = '5ae701122239'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename column is_committed to is_approved in collaboration_requests table
    op.alter_column('collaboration_requests', 'is_committed', new_column_name='is_approved')


def downgrade() -> None:
    """Downgrade schema."""
    # Rename column is_approved back to is_committed in collaboration_requests table
    op.alter_column('collaboration_requests', 'is_approved', new_column_name='is_committed')
