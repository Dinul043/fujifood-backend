"""Create user_addresses table

Revision ID: 011
Revises: 010
Create Date: 2026-07-13
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import CHAR

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_addresses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uuid", CHAR(36), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(50), nullable=False, server_default="Home"),
        sa.Column("address_line1", sa.String(300), nullable=False),
        sa.Column("address_line2", sa.String(300), nullable=True),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("state", sa.String(100), nullable=False),
        sa.Column("pincode", sa.String(10), nullable=False),
        sa.Column("landmark", sa.String(200), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid", name="uq_user_addresses_uuid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_user_addresses_tenant_id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_user_addresses_user_id"),
    )
    op.create_index("idx_user_addresses_user", "user_addresses", ["tenant_id", "user_id"])
    op.create_index("idx_user_addresses_deleted_at", "user_addresses", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("idx_user_addresses_deleted_at", table_name="user_addresses")
    op.drop_index("idx_user_addresses_user", table_name="user_addresses")
    op.drop_table("user_addresses")
