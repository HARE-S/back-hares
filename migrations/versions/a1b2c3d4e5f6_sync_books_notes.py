"""sync books notes columns

Revision ID: a1b2c3d4e5f6
Revises: d759ec76f0af
Create Date: 2026-09-11

Los campos copies_note y sessions_note (mantenimiento de libros, BE-16)
nunca pasaron a la BD. Los añade sin alterar la migración inicial.
"""
from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "d759ec76f0af"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add the missing book note columns."""
    op.add_column("books", sa.Column("copies_note", sa.String(length=255), nullable=True))
    op.add_column("books", sa.Column("sessions_note", sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Drop the columns added in upgrade()."""
    op.drop_column("books", "sessions_note")
    op.drop_column("books", "copies_note")