"""Create password_reset_tokens table

Revision ID: 014
Revises: 013
Create Date: 2026-07-13
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import CHAR

revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uuid", CHAR(36), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("otp", sa.String(6), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("is_used", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid", name="uq_password_reset_tokens_uuid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_password_reset_tokens_tenant_id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_password_reset_tokens_user_id"),
    )
    op.create_index("idx_password_reset_tokens_email", "password_reset_tokens", ["email"])
    op.create_index("idx_password_reset_tokens_user_id", "password_reset_tokens", ["user_id"])


def downgrade() -> None:
    op.drop_index("idx_password_reset_tokens_user_id", table_name="password_reset_tokens")
    op.drop_index("idx_password_reset_tokens_email", table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")
