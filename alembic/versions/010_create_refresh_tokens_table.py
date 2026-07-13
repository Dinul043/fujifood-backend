"""Create refresh_tokens table

Revision ID: 010
Revises: 009
Create Date: 2026-07-13
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import CHAR

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uuid", CHAR(36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid", name="uq_refresh_tokens_uuid"),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_refresh_tokens_user_id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_refresh_tokens_tenant_id"),
    )
    op.create_index("idx_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("idx_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])
    op.create_index("idx_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])


def downgrade() -> None:
    op.drop_index("idx_refresh_tokens_expires_at", table_name="refresh_tokens")
    op.drop_index("idx_refresh_tokens_token_hash", table_name="refresh_tokens")
    op.drop_index("idx_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
