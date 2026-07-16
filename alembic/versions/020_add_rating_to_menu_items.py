"""Add avg_rating and rating_count to menu_items, and is_bestseller flag.

Revision ID: 020
Revises: 019
"""
from alembic import op
import sqlalchemy as sa

revision = '020'
down_revision = '019'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('menu_items', sa.Column('avg_rating', sa.Float(), nullable=False, server_default='0'))
    op.add_column('menu_items', sa.Column('rating_count', sa.Integer(), nullable=False, server_default='0'))
    # is_bestseller might already exist, add if not
    try:
        op.add_column('menu_items', sa.Column('is_bestseller', sa.Boolean(), nullable=False, server_default='0'))
    except:
        pass


def downgrade() -> None:
    op.drop_column('menu_items', 'avg_rating')
    op.drop_column('menu_items', 'rating_count')
    op.drop_column('menu_items', 'is_bestseller')
