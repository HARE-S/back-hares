"""Remove birth_date and gender from students table.

Revision ID: 007_remove_birth_date_and_gender_from_students
Revises: 006_add_origin_to_masters
Create Date: 2026-09-23 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '007_remove_birth_date_and_gender_from_students'
down_revision = '006_add_origin_to_masters'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('students', 'gender')
    op.drop_column('students', 'birth_date')


def downgrade():
    op.add_column('students', sa.Column('birth_date', sa.Date(), nullable=True))
    op.add_column('students', sa.Column('gender', sa.String(20), nullable=True))
