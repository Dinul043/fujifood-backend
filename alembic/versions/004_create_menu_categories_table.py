"""Create menu_categories table

Revision ID: 004
Revises: 003
Create Date: 2026-07-13
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import CHAR

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "menu_categories",
        # Primary key
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uuid", CHAR(36), nullable=False),

        # Foreign keys
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),

        # Category info
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),

        # Audit columns
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),

        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid", name="uq_menu_categories_uuid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_menu_categories_tenant_id"),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], name="fk_menu_categories_restaurant_id"),
    )

    # Indexes
    op.create_index("idx_menu_categories_tenant_id", "menu_categories", ["tenant_id"])
    op.create_index("idx_menu_categories_restaurant_id", "menu_categories", ["restaurant_id"])
    op.create_index("idx_menu_categories_sort_order", "menu_categories", ["tenant_id", "sort_order"])
    op.create_index("idx_menu_categories_deleted_at", "menu_categories", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("idx_menu_categories_deleted_at", table_name="menu_categories")
    op.drop_index("idx_menu_categories_sort_order", table_name="menu_categories")
    op.drop_index("idx_menu_categories_restaurant_id", table_name="menu_categories")
    op.drop_index("idx_menu_categories_tenant_id", table_name="menu_categories")
    op.drop_table("menu_categories")
