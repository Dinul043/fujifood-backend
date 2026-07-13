"""Create order_items table

Revision ID: 007
Revises: 006
Create Date: 2026-07-13
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import CHAR

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uuid", CHAR(36), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("menu_item_id", sa.Integer(), nullable=False),
        sa.Column("item_name", sa.String(300), nullable=False),
        sa.Column("item_price", sa.Float(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("line_total", sa.Float(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        # Audit columns
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),

        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid", name="uq_order_items_uuid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_order_items_tenant_id"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], name="fk_order_items_order_id"),
        sa.ForeignKeyConstraint(["menu_item_id"], ["menu_items.id"], name="fk_order_items_menu_item_id"),
    )

    # Indexes
    op.create_index("idx_order_items_tenant_id", "order_items", ["tenant_id"])
    op.create_index("idx_order_items_order_id", "order_items", ["order_id"])
    op.create_index("idx_order_items_menu_item_id", "order_items", ["menu_item_id"])
    op.create_index("idx_order_items_deleted_at", "order_items", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("idx_order_items_deleted_at", table_name="order_items")
    op.drop_index("idx_order_items_menu_item_id", table_name="order_items")
    op.drop_index("idx_order_items_order_id", table_name="order_items")
    op.drop_index("idx_order_items_tenant_id", table_name="order_items")
    op.drop_table("order_items")
