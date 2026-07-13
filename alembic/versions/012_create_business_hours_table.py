"""Create business_hours table

Revision ID: 012
Revises: 011
Create Date: 2026-07-13
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import CHAR

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "business_hours",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uuid", CHAR(36), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("is_open", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("open_time", sa.String(5), nullable=True),
        sa.Column("close_time", sa.String(5), nullable=True),
        sa.Column("open_time_2", sa.String(5), nullable=True),
        sa.Column("close_time_2", sa.String(5), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid", name="uq_business_hours_uuid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_business_hours_tenant_id"),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], name="fk_business_hours_restaurant_id"),
    )
    op.create_index("idx_business_hours_restaurant_day", "business_hours", ["restaurant_id", "day_of_week"], unique=True)
    op.create_index("idx_business_hours_tenant_id", "business_hours", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("idx_business_hours_tenant_id", table_name="business_hours")
    op.drop_index("idx_business_hours_restaurant_day", table_name="business_hours")
    op.drop_table("business_hours")
