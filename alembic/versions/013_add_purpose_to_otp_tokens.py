"""Add purpose column to otp_tokens table

Revision ID: 013
Revises: 012
Create Date: 2026-07-13
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("otp_tokens", sa.Column("purpose", sa.String(20), nullable=False, server_default="login"))
    op.create_index("idx_otp_tokens_purpose", "otp_tokens", ["purpose"])


def downgrade() -> None:
    op.drop_index("idx_otp_tokens_purpose", table_name="otp_tokens")
    op.drop_column("otp_tokens", "purpose")
