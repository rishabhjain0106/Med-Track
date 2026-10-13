"""initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Hospitals
    op.create_table(
        'hospitals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('lat', sa.Float(), nullable=False),
        sa.Column('lng', sa.Float(), nullable=False),
        sa.Column('address', sa.String(length=500), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_hospitals_id'), 'hospitals', ['id'], unique=False)

    # Users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('hospital_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['hospital_id'], ['hospitals.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Blood Inventory
    op.create_table(
        'blood_inventory',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('hospital_id', sa.Integer(), nullable=False),
        sa.Column('blood_group', sa.String(length=10), nullable=False),
        sa.Column('units_available', sa.Integer(), nullable=False),
        sa.Column('expiry_date', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['hospital_id'], ['hospitals.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('hospital_id', 'blood_group', name='uq_hospital_blood_group')
    )
    op.create_index(op.f('ix_blood_inventory_blood_group'), 'blood_inventory', ['blood_group'], unique=False)
    op.create_index(op.f('ix_blood_inventory_hospital_id'), 'blood_inventory', ['hospital_id'], unique=False)
    op.create_index(op.f('ix_blood_inventory_id'), 'blood_inventory', ['id'], unique=False)

    # Medicine Inventory
    op.create_table(
        'medicine_inventory',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('hospital_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('quantity_available', sa.Integer(), nullable=False),
        sa.Column('expiry_date', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['hospital_id'], ['hospitals.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('hospital_id', 'name', name='uq_hospital_medicine_name')
    )
    op.create_index(op.f('ix_medicine_inventory_hospital_id'), 'medicine_inventory', ['hospital_id'], unique=False)
    op.create_index(op.f('ix_medicine_inventory_id'), 'medicine_inventory', ['id'], unique=False)
    op.create_index(op.f('ix_medicine_inventory_name'), 'medicine_inventory', ['name'], unique=False)

    # Bed Inventory
    op.create_table(
        'bed_inventory',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('hospital_id', sa.Integer(), nullable=False),
        sa.Column('bed_type', sa.String(length=50), nullable=False),
        sa.Column('total_beds', sa.Integer(), nullable=False),
        sa.Column('available_beds', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['hospital_id'], ['hospitals.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('hospital_id', 'bed_type', name='uq_hospital_bed_type')
    )
    op.create_index(op.f('ix_bed_inventory_bed_type'), 'bed_inventory', ['bed_type'], unique=False)
    op.create_index(op.f('ix_bed_inventory_hospital_id'), 'bed_inventory', ['hospital_id'], unique=False)
    op.create_index(op.f('ix_bed_inventory_id'), 'bed_inventory', ['id'], unique=False)

    # Reservations
    op.create_table(
        'reservations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('hospital_id', sa.Integer(), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_ref', sa.String(length=200), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['hospital_id'], ['hospitals.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reservations_created_at'), 'reservations', ['created_at'], unique=False)
    op.create_index(op.f('ix_reservations_hospital_id'), 'reservations', ['hospital_id'], unique=False)
    op.create_index(op.f('ix_reservations_id'), 'reservations', ['id'], unique=False)
    op.create_index(op.f('ix_reservations_resource_ref'), 'reservations', ['resource_ref'], unique=False)
    op.create_index(op.f('ix_reservations_resource_type'), 'reservations', ['resource_type'], unique=False)
    op.create_index(op.f('ix_reservations_status'), 'reservations', ['status'], unique=False)
    op.create_index(op.f('ix_reservations_user_id'), 'reservations', ['user_id'], unique=False)

    # Audit Logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('performed_by_id', sa.Integer(), nullable=True),
        sa.Column('hospital_id', sa.Integer(), nullable=True),
        sa.Column('reservation_id', sa.Integer(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['hospital_id'], ['hospitals.id'], ),
        sa.ForeignKeyConstraint(['performed_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['reservation_id'], ['reservations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('reservations')
    op.drop_table('bed_inventory')
    op.drop_table('medicine_inventory')
    op.drop_table('blood_inventory')
    op.drop_table('users')
    op.drop_table('hospitals')
