"""add planning tables

Revision ID: b6f9b7f74b31
Revises: 7087e6a255d9
Create Date: 2026-03-24
"""
from alembic import op
import sqlalchemy as sa


revision = 'b6f9b7f74b31'
down_revision = '7087e6a255d9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'hospital_capacities',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('hospital_id', sa.Integer(), sa.ForeignKey('hospitals.id'), nullable=False, unique=True),
        sa.Column('bed_count', sa.Integer(), nullable=True),
        sa.Column('doctor_count', sa.Integer(), nullable=True),
        sa.Column('nurse_count', sa.Integer(), nullable=True),
        sa.Column('ambulance_count', sa.Integer(), nullable=True),
        sa.Column('has_emergency_unit', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('has_operating_theatre', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('has_icu', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('has_blood_bank', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index(op.f('ix_hospital_capacities_id'), 'hospital_capacities', ['id'], unique=False)
    op.create_index(op.f('ix_hospital_capacities_hospital_id'), 'hospital_capacities', ['hospital_id'], unique=True)

    op.create_table(
        'lga_profiles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('state', sa.String(length=120), nullable=False),
        sa.Column('lga', sa.String(length=120), nullable=False),
        sa.Column('population', sa.Integer(), nullable=True),
        sa.Column('average_road_speed_kph', sa.Float(), nullable=True),
        sa.Column('road_access_factor', sa.Float(), nullable=True),
        sa.Column('rurality_index', sa.Float(), nullable=True),
        sa.Column('source', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('state', 'lga', name='uq_lga_profile_state_lga'),
    )
    op.create_index(op.f('ix_lga_profiles_id'), 'lga_profiles', ['id'], unique=False)
    op.create_index(op.f('ix_lga_profiles_lga'), 'lga_profiles', ['lga'], unique=False)
    op.create_index(op.f('ix_lga_profiles_state'), 'lga_profiles', ['state'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_lga_profiles_state'), table_name='lga_profiles')
    op.drop_index(op.f('ix_lga_profiles_lga'), table_name='lga_profiles')
    op.drop_index(op.f('ix_lga_profiles_id'), table_name='lga_profiles')
    op.drop_table('lga_profiles')
    op.drop_index(op.f('ix_hospital_capacities_hospital_id'), table_name='hospital_capacities')
    op.drop_index(op.f('ix_hospital_capacities_id'), table_name='hospital_capacities')
    op.drop_table('hospital_capacities')
