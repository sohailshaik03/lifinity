"""add expiry_records and waste_records extended fields

Revision ID: 20251213_add_expiry_waste_fields
Revises: 20251213_add_markdown_fields
Create Date: 2025-12-13 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '20251213_add_expiry_waste_fields'
down_revision = '20251213_add_markdown_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # expiry_records additions
    op.add_column('expiry_records', sa.Column('batch_number', sa.String(length=100), nullable=True))
    op.add_column('expiry_records', sa.Column('quantity_received', sa.Integer(), nullable=True))
    op.add_column('expiry_records', sa.Column('quantity_remaining', sa.Integer(), nullable=True))
    op.add_column('expiry_records', sa.Column('expiry_date', sa.DateTime(), nullable=True))
    op.add_column('expiry_records', sa.Column('received_date', sa.DateTime(), nullable=True))
    op.add_column('expiry_records', sa.Column('days_left', sa.Integer(), nullable=True))
    op.add_column('expiry_records', sa.Column('status', sa.String(length=32), nullable=True))
    op.add_column('expiry_records', sa.Column('created_at', sa.DateTime(), nullable=True))

    # waste_records additions
    op.add_column('waste_records', sa.Column('expiry_record_id', sa.Integer(), nullable=True))
    op.add_column('waste_records', sa.Column('reason', sa.String(length=255), nullable=True))
    op.add_column('waste_records', sa.Column('recorded_by', sa.Integer(), nullable=True))
    op.add_column('waste_records', sa.Column('recorded_at', sa.DateTime(), nullable=True))

    # best-effort FKs
    try:
        op.create_foreign_key('fk_waste_expiry', 'waste_records', 'expiry_records', ['expiry_record_id'], ['id'])
    except Exception:
        pass


def downgrade() -> None:
    try:
        op.drop_constraint('fk_waste_expiry', 'waste_records', type_='foreignkey')
    except Exception:
        pass

    for col in ['recorded_at','recorded_by','reason','expiry_record_id']:
        try:
            op.drop_column('waste_records', col)
        except Exception:
            pass

    for col in ['created_at','status','days_left','received_date','expiry_date','quantity_remaining','quantity_received','batch_number']:
        try:
            op.drop_column('expiry_records', col)
        except Exception:
            pass
