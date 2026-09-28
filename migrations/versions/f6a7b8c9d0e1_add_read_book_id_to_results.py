"""Add read_book_id to results table and backfill references

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-09-28 03:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Agregar columna read_book_id en results
    op.add_column('results', sa.Column('read_book_id', sa.Uuid(), nullable=True))

    # 2. Crear foreign key hacia read_books con ON DELETE SET NULL
    op.create_foreign_key(
        'results_read_book_id_fkey',
        'results',
        'read_books',
        ['read_book_id'],
        ['id'],
        ondelete='SET NULL',
    )

    # 3. Crear índice para optimizar búsquedas por lectura
    op.create_index('ix_results_read_book_id', 'results', ['read_book_id'], unique=False)

    # 4. Enlazar datos existentes en results a read_books
    op.execute("""
        UPDATE results r
        SET read_book_id = rb.id
        FROM read_books rb
        WHERE rb.student_id = r.student_id 
          AND rb.test_id = r.test_id
          AND r.read_book_id IS NULL;
    """)


def downgrade() -> None:
    op.drop_index('ix_results_read_book_id', table_name='results')
    op.drop_constraint('results_read_book_id_fkey', 'results', type_='foreignkey')
    op.drop_column('results', 'read_book_id')
