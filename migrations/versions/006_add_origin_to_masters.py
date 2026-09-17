"""Add origin field to students, centers and sections (BE-50).

Revision ID: 006_add_origin_to_masters
Revises: 005_create_audit_logs_table
Create Date: 2026-09-16 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '006_add_origin_to_masters'
down_revision = '005_create_audit_logs_table'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('students', sa.Column('origin', sa.String(20), nullable=False, server_default='alexia'))
    op.add_column('centers', sa.Column('origin', sa.String(20), nullable=False, server_default='alexia'))
    op.add_column('sections', sa.Column('origin', sa.String(20), nullable=False, server_default='alexia'))


def downgrade():
    op.drop_column('sections', 'origin')
    op.drop_column('centers', 'origin')
    op.drop_column('students', 'origin')
