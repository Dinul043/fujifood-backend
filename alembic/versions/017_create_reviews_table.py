"""Create reviews table.

Revision ID: 017
Revises: 016
"""
from alembic import op
import sqlalchemy as sa

revision = '017'
down_revision = '016'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'reviews',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('uuid', sa.String(36), nullable=False, unique=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id'), nullable=False, unique=True),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('customer_name', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('reviews')
