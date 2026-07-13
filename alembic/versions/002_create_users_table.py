"""Create users table

Revision ID: 002
Revises: 001
Create Date: 2026-07-13
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import CHAR

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        # Primary key
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uuid", CHAR(36), nullable=False),

        # Tenant FK
        sa.Column("tenant_id", sa.Integer(), nullable=False),

        # Identity
        sa.Column("name", sa.String(200), nullable=True),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),

        # Auth
        sa.Column("password_hash", sa.String(255), nullable=True),

        # Role and status
        sa.Column("role", sa.String(30), nullable=False, server_default="customer"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),

        # Flags
        sa.Column("phone_verified", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),

        # Audit columns
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),

        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid", name="uq_users_uuid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_users_tenant_id"),
    )

    # Indexes
    op.create_index("idx_users_tenant_id", "users", ["tenant_id"])
    op.create_index("idx_users_role", "users", ["role"])
    op.create_index("idx_users_deleted_at", "users", ["deleted_at"])
    op.create_index("idx_users_tenant_phone", "users", ["tenant_id", "phone"], unique=True)
    op.create_index("idx_users_tenant_role", "users", ["tenant_id", "role"])


def downgrade() -> None:
    op.drop_index("idx_users_tenant_role", table_name="users")
    op.drop_index("idx_users_tenant_phone", table_name="users")
    op.drop_index("idx_users_deleted_at", table_name="users")
    op.drop_index("idx_users_role", table_name="users")
    op.drop_index("idx_users_tenant_id", table_name="users")
    op.drop_table("users")
