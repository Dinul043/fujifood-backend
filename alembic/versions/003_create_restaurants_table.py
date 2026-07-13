"""Create restaurants table

Revision ID: 003
Revises: 002
Create Date: 2026-07-13
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import CHAR

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "restaurants",
        # Primary key
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uuid", CHAR(36), nullable=False),

        # Tenant FK
        sa.Column("tenant_id", sa.Integer(), nullable=False),

        # Business info
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cuisine_type", sa.String(200), nullable=True),
        sa.Column("gstin", sa.String(20), nullable=True),
        sa.Column("fssai_number", sa.String(20), nullable=True),

        # Location
        sa.Column("address_line1", sa.String(300), nullable=False),
        sa.Column("address_line2", sa.String(300), nullable=True),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("state", sa.String(100), nullable=False),
        sa.Column("pincode", sa.String(10), nullable=False),
        sa.Column("country", sa.String(50), nullable=False, server_default="India"),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),

        # Contact
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("website", sa.String(255), nullable=True),

        # Branding
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("banner_url", sa.String(500), nullable=True),
        sa.Column("favicon_url", sa.String(500), nullable=True),

        # Delivery settings
        sa.Column("delivery_radius_km", sa.Float(), nullable=False, server_default=sa.text("5.0")),
        sa.Column("min_order_amount", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("delivery_fee", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("free_delivery_above", sa.Float(), nullable=True),
        sa.Column("avg_delivery_time_mins", sa.Integer(), nullable=False, server_default=sa.text("30")),

        # Operational
        sa.Column("is_online", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.text("0")),

        # SEO
        sa.Column("seo_title", sa.String(200), nullable=True),
        sa.Column("seo_description", sa.String(500), nullable=True),
        sa.Column("seo_keywords", sa.String(500), nullable=True),

        # Audit columns
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),

        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid", name="uq_restaurants_uuid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_restaurants_tenant_id"),
    )

    # Indexes
    op.create_index("idx_restaurants_tenant_id", "restaurants", ["tenant_id"])
    op.create_index("idx_restaurants_city", "restaurants", ["city"])
    op.create_index("idx_restaurants_is_online", "restaurants", ["is_online"])
    op.create_index("idx_restaurants_deleted_at", "restaurants", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("idx_restaurants_deleted_at", table_name="restaurants")
    op.drop_index("idx_restaurants_is_online", table_name="restaurants")
    op.drop_index("idx_restaurants_city", table_name="restaurants")
    op.drop_index("idx_restaurants_tenant_id", table_name="restaurants")
    op.drop_table("restaurants")
