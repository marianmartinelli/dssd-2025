"""add organizations table and organization_id to users and projects and status to projects

Revision ID: 3ffe1b861942
Revises: 2a6985fd3004
Create Date: 2025-11-18 08:44:39.614107

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3ffe1b861942'
down_revision: Union[str, Sequence[str], None] = '2a6985fd3004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organizations_id'), 'organizations', ['id'], unique=False)
    op.create_index(op.f('ix_organizations_name'), 'organizations', ['name'], unique=True)

    # Add organization_id to users table
    op.add_column('users', sa.Column('organization_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_users_organization_id', 'users', 'organizations', ['organization_id'], ['id'])

    # Add organization_id and status to projects table
    op.add_column('projects', sa.Column('organization_id', sa.Integer(), nullable=True))
    op.add_column('projects', sa.Column('status', sa.String(), nullable=False, server_default='in_progress'))
    op.create_foreign_key('fk_projects_organization_id', 'projects', 'organizations', ['organization_id'], ['id'])

    # Insert default organization
    op.execute("""
        INSERT INTO organizations (id, name, description, created_at)
        VALUES (1, 'Default Organization', 'Default organization for existing users', NOW())
    """)

    # Update existing user to belong to default organization
    op.execute("""
        UPDATE users SET organization_id = 1 WHERE username = 'dssd'
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop foreign keys
    op.drop_constraint('fk_projects_organization_id', 'projects', type_='foreignkey')
    op.drop_constraint('fk_users_organization_id', 'users', type_='foreignkey')

    # Drop columns from projects
    op.drop_column('projects', 'status')
    op.drop_column('projects', 'organization_id')

    # Drop column from users
    op.drop_column('users', 'organization_id')

    # Drop organizations table
    op.drop_index(op.f('ix_organizations_name'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_id'), table_name='organizations')
    op.drop_table('organizations')
