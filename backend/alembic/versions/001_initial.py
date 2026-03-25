"""initial schema"""
from alembic import op
import sqlalchemy as sa

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'hospitals',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('state', sa.String(length=120), nullable=False),
        sa.Column('city', sa.String(length=120), nullable=False),
        sa.Column('address', sa.String(length=255), nullable=False),
        sa.Column('specialties', sa.Text(), nullable=False),
        sa.Column('services', sa.Text(), nullable=False),
        sa.Column('capabilities', sa.Text(), nullable=False),
        sa.Column('phone', sa.String(length=40), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'appointments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('hospital_id', sa.Integer(), sa.ForeignKey('hospitals.id'), nullable=False),
        sa.Column('patient_name', sa.String(length=150), nullable=False),
        sa.Column('patient_email', sa.String(length=255), nullable=False),
        sa.Column('patient_phone', sa.String(length=40), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('scheduled_for', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('payment_status', sa.String(length=30), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('appointment_id', sa.Integer(), sa.ForeignKey('appointments.id'), nullable=False),
        sa.Column('txn_ref', sa.String(length=120), nullable=False, unique=True),
        sa.Column('amount_kobo', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('provider_response_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('payments')
    op.drop_table('appointments')
    op.drop_table('hospitals')
