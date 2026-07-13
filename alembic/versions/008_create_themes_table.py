"""Create themes table

Revision ID: 008
Revises: 007
Create Date: 2026-07-13
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import CHAR

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "themes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uuid", CHAR(36), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        # Typography
        sa.Column("font_heading", sa.String(100), nullable=False,
                  server_default="Plus Jakarta Sans"),
        sa.Column("font_body", sa.String(100), nullable=False,
                  server_default="Inter"),
        # Colors
        sa.Column("color_primary", sa.String(20), nullable=False,
                  server_default="#E85D8E"),
        sa.Column("color_secondary", sa.String(20), nullable=False,
                  server_default="#18181B"),
        sa.Column("color_accent", sa.String(20), nullable=False,
                  server_default="#F59E0B"),
        sa.Column("color_bg", sa.String(20), nullable=False,
                  server_default="#FAFAFA"),
        sa.Column("color_surface", sa.String(20), nullable=False,
                  server_default="#FFFFFF"),
        sa.Column("color_text", sa.String(20), nullable=False,
                  server_default="#18181B"),
        # Layout
        sa.Column("hero_layout", sa.String(50), nullable=False,
                  server_default="split"),
        sa.Column("header_style", sa.String(50), nullable=False,
                  server_default="glass"),
        sa.Column("card_style", sa.String(50), nullable=False,
                  server_default="rounded"),
        # Media
        sa.Column("hero_image_url", sa.String(500), nullable=True),
        sa.Column("hero_video_url", sa.String(500), nullable=True),
        # Custom
        sa.Column("custom_css", sa.Text(), nullable=True),
        sa.Column("advanced_config", sa.JSON(), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=False,
                  server_default=sa.text("1")),
        # Audit columns
        sa.Column("created_at", sa.DateTime(), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid", name="uq_themes_uuid"),
        sa.UniqueConstraint("tenant_id", name="uq_themes_tenant_id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"],
                                name="fk_themes_tenant_id"),
    )

    op.create_index("idx_themes_tenant_id", "themes", ["tenant_id"])
    op.create_index("idx_themes_deleted_at", "themes", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("idx_themes_deleted_at", table_name="themes")
    op.drop_index("idx_themes_tenant_id", table_name="themes")
    op.drop_table("themes")
