"""Create orders table

Revision ID: 006
Revises: 005
Create Date: 2026-07-13
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import CHAR

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "orders",
        # Primary key
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uuid", CHAR(36), nullable=False),

        # Foreign keys
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),

        # Order identity
        sa.Column("order_number", sa.String(50), nullable=False),

        # Status
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),

        # Amounts
        sa.Column("subtotal", sa.Float(), nullable=False),
        sa.Column("delivery_fee", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("discount_amount", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("tax_amount", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("total_amount", sa.Float(), nullable=False),

        # Payment
        sa.Column("payment_method", sa.String(20), nullable=False, server_default="cod"),
        sa.Column("payment_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("payment_ref", sa.String(200), nullable=True),

        # Delivery address (JSON snapshot)
        sa.Column("delivery_address", sa.JSON(), nullable=False),

        # Timing
        sa.Column("estimated_delivery_time", sa.Integer(), nullable=True),
        sa.Column("accepted_at", sa.String(50), nullable=True),
        sa.Column("prepared_at", sa.String(50), nullable=True),
        sa.Column("delivered_at", sa.String(50), nullable=True),

        # Notes
        sa.Column("customer_notes", sa.Text(), nullable=True),
        sa.Column("restaurant_notes", sa.Text(), nullable=True),

        # Audit columns
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),

        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid", name="uq_orders_uuid"),
        sa.UniqueConstraint("order_number", name="uq_orders_order_number"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_orders_tenant_id"),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], name="fk_orders_restaurant_id"),
        sa.ForeignKeyConstraint(["customer_id"], ["users.id"], name="fk_orders_customer_id"),
    )

    # Indexes
    op.create_index("idx_orders_tenant_id", "orders", ["tenant_id"])
    op.create_index("idx_orders_restaurant_id", "orders", ["restaurant_id"])
    op.create_index("idx_orders_customer_id", "orders", ["customer_id"])
    op.create_index("idx_orders_order_number", "orders", ["order_number"])
    op.create_index("idx_orders_status", "orders", ["tenant_id", "status"])
    op.create_index("idx_orders_payment_status", "orders", ["tenant_id", "payment_status"])
    op.create_index("idx_orders_created_at", "orders", ["tenant_id", "created_at"])
    op.create_index("idx_orders_deleted_at", "orders", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("idx_orders_deleted_at", table_name="orders")
    op.drop_index("idx_orders_created_at", table_name="orders")
    op.drop_index("idx_orders_payment_status", table_name="orders")
    op.drop_index("idx_orders_status", table_name="orders")
    op.drop_index("idx_orders_order_number", table_name="orders")
    op.drop_index("idx_orders_customer_id", table_name="orders")
    op.drop_index("idx_orders_restaurant_id", table_name="orders")
    op.drop_index("idx_orders_tenant_id", table_name="orders")
    op.drop_table("orders")
