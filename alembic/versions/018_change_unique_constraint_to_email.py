"""Change unique constraint from phone to email per tenant.

Phone can be shared by multiple users (family members etc).
Email is the true unique identifier for customers.

Revision ID: 018
Revises: 017
"""
from alembic import op

revision = '018'
down_revision = '017'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the old phone-based unique index
    op.drop_index('idx_users_tenant_phone', table_name='users')
    # Create a non-unique index on phone (for lookups)
    op.create_index('idx_users_tenant_phone', 'users', ['tenant_id', 'phone'], unique=False)
    # Email unique constraint already exists from migration 015


def downgrade() -> None:
    op.drop_index('idx_users_tenant_phone', table_name='users')
    op.create_index('idx_users_tenant_phone', 'users', ['tenant_id', 'phone'], unique=True)
