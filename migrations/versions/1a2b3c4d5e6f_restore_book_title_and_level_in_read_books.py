"""Restore book_title and level in read_books and make test_id optional

Revision ID: 1a2b3c4d5e6f
Revises: f6a7b8c9d0e1
Create Date: 2026-09-28 08:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a2b3c4d5e6f'
down_revision: Union[str, None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Agregar columnas book_title y level
    op.add_column('read_books', sa.Column('book_title', sa.String(255), nullable=True))
    op.add_column('read_books', sa.Column('level', sa.String(20), nullable=False, server_default='0'))

    # 2. Poblar book_title y level a partir de tests para filas existentes
    op.execute("""
        UPDATE read_books rb
        SET book_title = t.name,
            level = CASE 
                WHEN t.test_letter IN ('0', '0-I', 'I', 'I/II', 'II') THEN t.test_letter 
                WHEN t.course::text IN ('0', '0-I', 'I', 'I/II', 'II') THEN t.course::text
                ELSE '0' 
            END
        FROM tests t
        WHERE rb.test_id = t.id;
    """)

    op.execute("""
        UPDATE read_books
        SET book_title = 'Libro de lectura'
        WHERE book_title IS NULL OR book_title = '';
    """)

    # 3. Hacer book_title NOT NULL
    op.alter_column('read_books', 'book_title', nullable=False)

    # 4. Hacer test_id NULLABLE y foreign key ON DELETE SET NULL
    op.alter_column('read_books', 'test_id', nullable=True)
    op.drop_constraint('read_books_test_id_fkey', 'read_books', type_='foreignkey')
    op.create_foreign_key(
        'read_books_test_id_fkey',
        'read_books',
        'tests',
        ['test_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # 5. Actualizar restricción de unicidad a (student_id, book_title, start_date)
    op.drop_constraint('uq_read_books_student_test_start', 'read_books', type_='unique')
    op.create_unique_constraint(
        'uq_read_books_student_title_start',
        'read_books',
        ['student_id', 'book_title', 'start_date']
    )


def downgrade() -> None:
    op.drop_constraint('uq_read_books_student_title_start', 'read_books', type_='unique')
    op.create_unique_constraint(
        'uq_read_books_student_test_start',
        'read_books',
        ['student_id', 'test_id', 'start_date']
    )
    op.alter_column('read_books', 'test_id', nullable=False)
    op.drop_column('read_books', 'level')
    op.drop_column('read_books', 'book_title')
