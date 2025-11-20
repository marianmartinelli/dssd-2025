"""add case_id to projects

Revision ID: b88b7d6ee0ca
Revises: bd4ea13bc6fb
Create Date: 2025-10-22 20:27:48.068489

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b88b7d6ee0ca'
down_revision: Union[str, Sequence[str], None] = 'bd4ea13bc6fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('projects', sa.Column('case_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('projects', 'case_id')
