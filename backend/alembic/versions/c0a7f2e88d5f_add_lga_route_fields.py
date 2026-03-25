"""add lga route fields

Revision ID: c0a7f2e88d5f
Revises: b6f9b7f74b31
Create Date: 2026-03-24
"""
from alembic import op
import sqlalchemy as sa


revision = 'c0a7f2e88d5f'
down_revision = 'b6f9b7f74b31'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('lga_profiles', sa.Column('centroid_latitude', sa.Float(), nullable=True))
    op.add_column('lga_profiles', sa.Column('centroid_longitude', sa.Float(), nullable=True))
    op.add_column('lga_profiles', sa.Column('nearest_hospital_registry_id', sa.String(length=255), nullable=True))
    op.add_column('lga_profiles', sa.Column('nearest_hospital_name', sa.String(length=255), nullable=True))
    op.add_column('lga_profiles', sa.Column('nearest_care_km', sa.Float(), nullable=True))
    op.add_column('lga_profiles', sa.Column('estimated_travel_time_minutes', sa.Integer(), nullable=True))
    op.add_column('lga_profiles', sa.Column('route_source', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('lga_profiles', 'route_source')
    op.drop_column('lga_profiles', 'estimated_travel_time_minutes')
    op.drop_column('lga_profiles', 'nearest_care_km')
    op.drop_column('lga_profiles', 'nearest_hospital_name')
    op.drop_column('lga_profiles', 'nearest_hospital_registry_id')
    op.drop_column('lga_profiles', 'centroid_longitude')
    op.drop_column('lga_profiles', 'centroid_latitude')
