"""add registry_id to hospitals

Revision ID: 3e83836883b1
Revises: 7087e6a255d9
Create Date: 2026-03-23 20:04:13.106414
"""
from alembic import op
import sqlalchemy as sa


revision = '3e83836883b1'
down_revision = '7087e6a255d9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('hospitals', sa.Column('registry_id', sa.String(255), nullable=True, unique=True, index=True))


def downgrade() -> None:
    op.drop_column('hospitals', 'registry_id')
