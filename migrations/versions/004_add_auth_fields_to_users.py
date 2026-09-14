"""Add lastname, password_hash, area to users table for local auth.

Revision ID: 004_add_auth_fields_to_users
Revises: 003_create_sessions_table
Create Date: 2026-09-14 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '004_add_auth_fields_to_users'
down_revision = '003_create_sessions_table'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('lastname', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('password_hash', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('area', sa.String(255), nullable=True))


def downgrade():
    op.drop_column('users', 'area')
    op.drop_column('users', 'password_hash')
    op.drop_column('users', 'lastname')
