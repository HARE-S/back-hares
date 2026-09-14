"""Create sessions table for BE-40.

Revision ID: 003_create_sessions_table
Revises: 002_add_area_created_by
Create Date: 2026-09-14 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '003_create_sessions_table'
down_revision = '002_add_area_created_by'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'sessions',
        sa.Column('id', sa.String(255), nullable=False, primary_key=True),
        sa.Column('user_id', sa.Uuid(as_uuid=True), nullable=False, index=True),
        sa.Column('user_email', sa.String(255), nullable=False),
        sa.Column('user_role', sa.String(20), nullable=False),
        sa.Column('user_area', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(), nullable=False, index=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )


def downgrade():
    op.drop_table('sessions')
