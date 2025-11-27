"""merge heads

Revision ID: d72168c3e854
Revises: 82dfdfb330e1, a1b2c3d4e5f6
Create Date: 2025-11-26 23:32:30.828678

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd72168c3e854'
down_revision: Union[str, Sequence[str], None] = ('82dfdfb330e1', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
