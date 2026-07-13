"""Create menu_items table

Revision ID: 005
Revises: 004
Create Date: 2026-07-13
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import CHAR

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "menu_items",
        # Primary key
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uuid", CHAR(36), nullable=False),

        # Foreign keys
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),

        # Basic info
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(500), nullable=True),

        # Pricing
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("discount_price", sa.Float(), nullable=True),

        # Classification
        sa.Column("food_type", sa.String(20), nullable=False, server_default="veg"),
        sa.Column("is_bestseller", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_recommended", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_spicy", sa.Boolean(), nullable=False, server_default=sa.text("0")),

        # Availability
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),

        # Nutritional info
        sa.Column("calories", sa.Integer(), nullable=True),
        sa.Column("allergens", sa.String(500), nullable=True),

        # SEO / Search
        sa.Column("tags", sa.String(500), nullable=True),

        # Audit columns
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),

        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid", name="uq_menu_items_uuid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_menu_items_tenant_id"),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], name="fk_menu_items_restaurant_id"),
        sa.ForeignKeyConstraint(["category_id"], ["menu_categories.id"], name="fk_menu_items_category_id"),
    )

    # Indexes
    op.create_index("idx_menu_items_tenant_id", "menu_items", ["tenant_id"])
    op.create_index("idx_menu_items_restaurant_id", "menu_items", ["restaurant_id"])
    op.create_index("idx_menu_items_category_id", "menu_items", ["category_id"])
    op.create_index("idx_menu_items_food_type", "menu_items", ["tenant_id", "food_type"])
    op.create_index("idx_menu_items_available", "menu_items", ["tenant_id", "is_available"])
    op.create_index("idx_menu_items_deleted_at", "menu_items", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("idx_menu_items_deleted_at", table_name="menu_items")
    op.drop_index("idx_menu_items_available", table_name="menu_items")
    op.drop_index("idx_menu_items_food_type", table_name="menu_items")
    op.drop_index("idx_menu_items_category_id", table_name="menu_items")
    op.drop_index("idx_menu_items_restaurant_id", table_name="menu_items")
    op.drop_index("idx_menu_items_tenant_id", table_name="menu_items")
    op.drop_table("menu_items")
