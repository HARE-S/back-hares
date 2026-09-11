"""Add course and test_letter to Test model (BE-52 preparation).

Revision ID: f1e2d3c4b5a6
Revises: a1b2c3d4e5f6
Create Date: 2026-09-11

"""
from alembic import op
import sqlalchemy as sa


revision = "f1e2d3c4b5a6"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    # Rename level to course and convert to Integer
    op.alter_column(
        "tests",
        "level",
        new_column_name="course",
        type_=sa.Integer(),
        existing_type=sa.String(length=20),
        postgresql_using="level::integer",
    )
    # Add test_letter column for pedagogical ordering (I, A, B, C, D, E)
    op.add_column("tests", sa.Column("test_letter", sa.String(length=5), nullable=True))


def downgrade():
    # Remove test_letter column
    op.drop_column("tests", "test_letter")
    # Revert course to level and convert back to String
    op.alter_column(
        "tests",
        "course",
        new_column_name="level",
        type_=sa.String(length=20),
        existing_type=sa.Integer(),
        postgresql_using="course::varchar",
    )
