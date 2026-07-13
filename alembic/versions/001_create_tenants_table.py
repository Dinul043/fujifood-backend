"""Create tenants table

Revision ID: 001
Revises: None
Create Date: 2026-07-13
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import CHAR

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        # Primary key
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uuid", CHAR(36), nullable=False),

        # Identity
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("custom_domain", sa.String(255), nullable=True),

        # Status & Plan
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("plan", sa.String(20), nullable=False, server_default="trial"),
        sa.Column("trial_ends_at", sa.String(50), nullable=True),
        sa.Column("subscription_ends_at", sa.String(50), nullable=True),

        # Owner contact
        sa.Column("owner_name", sa.String(200), nullable=False),
        sa.Column("owner_email", sa.String(255), nullable=False),
        sa.Column("owner_phone", sa.String(20), nullable=True),

        # Flags
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.text("0")),

        # Metadata
        sa.Column("onboarding_notes", sa.Text(), nullable=True),

        # Audit columns
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),

        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid", name="uq_tenants_uuid"),
        sa.UniqueConstraint("slug", name="uq_tenants_slug"),
        sa.UniqueConstraint("custom_domain", name="uq_tenants_custom_domain"),
        sa.UniqueConstraint("owner_email", name="uq_tenants_owner_email"),
    )

    # Indexes
    op.create_index("idx_tenants_status", "tenants", ["status"])
    op.create_index("idx_tenants_slug", "tenants", ["slug"])
    op.create_index("idx_tenants_owner_email", "tenants", ["owner_email"])
    op.create_index("idx_tenants_deleted_at", "tenants", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("idx_tenants_deleted_at", table_name="tenants")
    op.drop_index("idx_tenants_owner_email", table_name="tenants")
    op.drop_index("idx_tenants_slug", table_name="tenants")
    op.drop_index("idx_tenants_status", table_name="tenants")
    op.drop_table("tenants")
