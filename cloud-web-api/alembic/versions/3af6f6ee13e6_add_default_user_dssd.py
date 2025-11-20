"""add default user dssd

Revision ID: 3af6f6ee13e6
Revises: b88b7d6ee0ca
Create Date: 2025-10-22 20:32:32.932341

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from passlib.context import CryptContext


# revision identifiers, used by Alembic.
revision: str = '3af6f6ee13e6'
down_revision: Union[str, Sequence[str], None] = 'b88b7d6ee0ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def upgrade() -> None:
    """Upgrade schema."""
    # Hash the password using the same method as in app/core/security.py
    hashed_password = pwd_context.hash("entrega3")

    # Insert default user
    op.execute(
        f"""
        INSERT INTO users (username, email, hashed_password)
        VALUES ('dssd', 'dssd@example.com', '{hashed_password}')
        ON CONFLICT (username) DO NOTHING;
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove the default user
    op.execute("DELETE FROM users WHERE username = 'dssd';")

