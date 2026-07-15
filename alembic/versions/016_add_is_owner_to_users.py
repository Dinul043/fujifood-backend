"""Add is_owner column to users table.

Revision ID: 016
Revises: 015
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '016'
down_revision = '015'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_owner', sa.Boolean(), nullable=False, server_default='0'))
    # Set existing restaurant_admin (phone 9876543210) as owner
    op.execute("UPDATE users SET is_owner = 1 WHERE role = 'restaurant_admin' AND phone = '9876543210'")


def downgrade() -> None:
    op.drop_column('users', 'is_owner')
