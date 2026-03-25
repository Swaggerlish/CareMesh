"""add country to hospitals

Revision ID: 7087e6a255d9
Revises: 001_initial
Create Date: 2026-03-23 19:42:49.872145
"""
from alembic import op
import sqlalchemy as sa


revision = '7087e6a255d9'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('hospitals', sa.Column('country', sa.String(120), nullable=False, default='Nigeria', index=True))


def downgrade() -> None:
    op.drop_column('hospitals', 'country')
