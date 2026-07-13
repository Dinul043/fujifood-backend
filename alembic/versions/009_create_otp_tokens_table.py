"""Create otp_tokens table

Revision ID: 009
Revises: 008
Create Date: 2026-07-13
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import CHAR

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "otp_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uuid", CHAR(36), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
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
        sa.UniqueConstraint("uuid", name="uq_otp_tokens_uuid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_otp_tokens_tenant_id"),
    )
    op.create_index("idx_otp_tokens_tenant_phone", "otp_tokens", ["tenant_id", "phone"])
    op.create_index("idx_otp_tokens_expires_at", "otp_tokens", ["expires_at"])


def downgrade() -> None:
    op.drop_index("idx_otp_tokens_expires_at", table_name="otp_tokens")
    op.drop_index("idx_otp_tokens_tenant_phone", table_name="otp_tokens")
    op.drop_table("otp_tokens")
