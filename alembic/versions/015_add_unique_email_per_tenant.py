"""Add unique constraint on email per tenant in users table

Revision ID: 015
Revises: 014
Create Date: 2026-07-13
"""
from typing import Sequence, Union
from alembic import op

revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("idx_users_tenant_email", "users", ["tenant_id", "email"], unique=True)


def downgrade() -> None:
    op.drop_index("idx_users_tenant_email", table_name="users")
