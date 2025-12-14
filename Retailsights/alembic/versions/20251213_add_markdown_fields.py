"""add markdown_sales extra fields

Revision ID: 20251213_add_markdown_fields
Revises: 77dc5783bf0b
Create Date: 2025-12-13 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251213_add_markdown_fields'
down_revision = '77dc5783bf0b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('markdown_sales', sa.Column('product_id', sa.Integer(), nullable=True))
    op.add_column('markdown_sales', sa.Column('sku', sa.String(length=100), nullable=True))
    op.add_column('markdown_sales', sa.Column('original_price', sa.Float(), nullable=True))
    op.add_column('markdown_sales', sa.Column('discount_percent', sa.Float(), nullable=True))
    op.add_column('markdown_sales', sa.Column('discount_amount', sa.Float(), nullable=True))
    op.add_column('markdown_sales', sa.Column('rule_id', sa.Integer(), nullable=True))
    op.add_column('markdown_sales', sa.Column('rule_name', sa.String(length=255), nullable=True))
    op.add_column('markdown_sales', sa.Column('expiry_record_id', sa.Integer(), nullable=True))
    op.add_column('markdown_sales', sa.Column('sold_by', sa.Integer(), nullable=True))

    # create foreign keys where applicable (best-effort; if target tables missing this will still work on most DBs)
    try:
        op.create_foreign_key('fk_markdown_product', 'markdown_sales', 'products', ['product_id'], ['id'])
    except Exception:
        pass
    try:
        op.create_foreign_key('fk_markdown_expiry', 'markdown_sales', 'expiry_records', ['expiry_record_id'], ['id'])
    except Exception:
        pass
    try:
        op.create_foreign_key('fk_markdown_soldby', 'markdown_sales', 'users', ['sold_by'], ['id'])
    except Exception:
        pass


def downgrade() -> None:
    try:
        op.drop_constraint('fk_markdown_soldby', 'markdown_sales', type_='foreignkey')
    except Exception:
        pass
    try:
        op.drop_constraint('fk_markdown_expiry', 'markdown_sales', type_='foreignkey')
    except Exception:
        pass
    try:
        op.drop_constraint('fk_markdown_product', 'markdown_sales', type_='foreignkey')
    except Exception:
        pass

    op.drop_column('markdown_sales', 'sold_by')
    op.drop_column('markdown_sales', 'expiry_record_id')
    op.drop_column('markdown_sales', 'rule_name')
    op.drop_column('markdown_sales', 'rule_id')
    op.drop_column('markdown_sales', 'discount_amount')
    op.drop_column('markdown_sales', 'discount_percent')
    op.drop_column('markdown_sales', 'original_price')
    op.drop_column('markdown_sales', 'sku')
    op.drop_column('markdown_sales', 'product_id')
