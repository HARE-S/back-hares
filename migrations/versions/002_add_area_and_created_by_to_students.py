"""Add area and created_by_user_id to students table.

Revision ID: 002_add_area_created_by
Revises: 001_create_users_table
Create Date: 2026-09-14 12:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '002_add_area_created_by'
down_revision = '001_create_users_table'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('students', sa.Column('area', sa.String(255), nullable=False, server_default='Sin área'))
    op.add_column('students', sa.Column('created_by_user_id', sa.Uuid(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_students_created_by_user_id', 'students', 'users', ['created_by_user_id'], ondelete='SET NULL')


def downgrade():
    op.drop_constraint('fk_students_created_by_user_id', 'students', type_='foreignkey')
    op.drop_column('students', 'created_by_user_id')
    op.drop_column('students', 'area')
