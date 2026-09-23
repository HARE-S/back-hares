"""Add start_date, end_date, and sector to sections table.

Revision ID: 008_align_sections_with_penascal
Revises: 007_remove_birth_date_and_gender_from_students
Create Date: 2026-09-23 11:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '008_align_sections_with_penascal'
down_revision = '007_remove_birth_date_and_gender_from_students'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('sections', sa.Column('start_date', sa.Date(), nullable=True))
    op.add_column('sections', sa.Column('end_date', sa.Date(), nullable=True))
    op.add_column('sections', sa.Column('sector', sa.String(length=100), nullable=True))


def downgrade():
    op.drop_column('sections', 'sector')
    op.drop_column('sections', 'end_date')
    op.drop_column('sections', 'start_date')
