"""merge heads: observations and external_ref

Revision ID: ec1020344213
Revises: 82dfdfb330e1, a9c2e1d4f5b6
Create Date: 2025-11-27 16:25:09.554992

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ec1020344213'
down_revision: Union[str, Sequence[str], None] = ('82dfdfb330e1', 'a9c2e1d4f5b6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
