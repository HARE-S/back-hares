"""Link read_books to tests via test_id

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-09-28 02:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Eliminar restricción única por título
    op.drop_constraint('uq_read_books_student_title_start', 'read_books', type_='unique')

    # 2. Agregar columna test_id (nullable inicialmente para migrar datos existentes)
    op.add_column('read_books', sa.Column('test_id', sa.Uuid(), nullable=True))

    # 3. Asignar un test_id válido a registros existentes si los hay
    op.execute("""
        UPDATE read_books 
        SET test_id = (SELECT id FROM tests ORDER BY id LIMIT 1)
        WHERE test_id IS NULL AND EXISTS (SELECT 1 FROM tests);
    """)

    # Eliminar cualquier fila huérfana si tests estuviera vacío
    op.execute("DELETE FROM read_books WHERE test_id IS NULL;")

    # 4. Establecer test_id como NOT NULL y crear clave foránea
    op.alter_column('read_books', 'test_id', nullable=False)
    op.create_foreign_key(
        'read_books_test_id_fkey',
        'read_books',
        'tests',
        ['test_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # 5. Crear nueva restricción única por alumno, prueba y fecha de inicio
    op.create_unique_constraint(
        'uq_read_books_student_test_start',
        'read_books',
        ['student_id', 'test_id', 'start_date']
    )

    # 6. Crear índice sobre test_id
    op.create_index('ix_read_books_test_id', 'read_books', ['test_id'], unique=False)

    # 7. Eliminar columnas redundantes (el título y nivel se derivan de test)
    op.drop_column('read_books', 'book_title')
    op.drop_column('read_books', 'level')


def downgrade() -> None:
    op.add_column('read_books', sa.Column('level', sa.String(20), nullable=True))
    op.add_column('read_books', sa.Column('book_title', sa.String(255), nullable=True))

    op.execute("""
        UPDATE read_books rb
        SET book_title = t.name, level = '0'
        FROM tests t
        WHERE rb.test_id = t.id;
    """)

    op.alter_column('read_books', 'book_title', nullable=False)
    op.alter_column('read_books', 'level', nullable=False)

    op.drop_index('ix_read_books_test_id', table_name='read_books')
    op.drop_constraint('uq_read_books_student_test_start', 'read_books', type_='unique')
    op.drop_constraint('read_books_test_id_fkey', 'read_books', type_='foreignkey')
    op.drop_column('read_books', 'test_id')

    op.create_unique_constraint(
        'uq_read_books_student_title_start',
        'read_books',
        ['student_id', 'book_title', 'start_date']
    )
