"""Create audit_logs table for BE-44.

Revision ID: 005_create_audit_logs_table
Revises: 004_add_auth_fields_to_users
Create Date: 2026-09-14 13:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '005_create_audit_logs_table'
down_revision = '004_add_auth_fields_to_users'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Uuid(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('user_id', sa.Uuid(as_uuid=True), nullable=True, index=True),
        sa.Column('user_email', sa.String(255), nullable=False, index=True),
        sa.Column('action', sa.String(50), nullable=False, index=True),
        sa.Column('resource_type', sa.String(100), nullable=True),
        sa.Column('resource_id', sa.String(255), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='success'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), index=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    )


def downgrade():
    op.drop_table('audit_logs')
