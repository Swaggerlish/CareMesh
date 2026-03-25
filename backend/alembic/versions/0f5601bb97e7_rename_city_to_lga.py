"""rename city to lga

Revision ID: 0f5601bb97e7
Revises: 3e83836883b1
Create Date: 2026-03-23 20:12:38.652134
"""
from alembic import op
import sqlalchemy as sa


revision = '0f5601bb97e7'
down_revision = '3e83836883b1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('hospitals', 'city', new_column_name='lga')


def downgrade() -> None:
    op.alter_column('hospitals', 'lga', new_column_name='city')
