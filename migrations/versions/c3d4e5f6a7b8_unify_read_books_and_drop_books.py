"""unify read_books and drop books

Revision ID: c3d4e5f6a7b8
Revises: 2e988e9f4a06
Create Date: 2026-09-28 00:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'c3d4e5f6a7b8'
down_revision = '2e988e9f4a06'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Drop trigger and function if exists
    op.execute("DROP TRIGGER IF EXISTS trg_sync_book_to_test ON books;")
    op.execute("DROP FUNCTION IF EXISTS sync_book_to_test();")
    op.execute("DROP TRIGGER IF EXISTS trg_sync_test_to_book ON tests;")
    op.execute("DROP FUNCTION IF EXISTS sync_test_to_book();")

    # 2. Modify read_books
    op.drop_constraint('read_books_book_id_fkey', 'read_books', type_='foreignkey')
    op.drop_constraint('uq_read_books_student_book_start', 'read_books', type_='unique')
    op.drop_column('read_books', 'book_id')

    op.add_column('read_books', sa.Column('book_title', sa.String(length=255), nullable=False, server_default=''))
    op.alter_column('read_books', 'book_title', server_default=None)
    op.add_column('read_books', sa.Column('level', sa.String(length=20), nullable=False, server_default='0'))
    op.add_column('read_books', sa.Column('copies_note', sa.String(length=255), nullable=True))
    op.add_column('read_books', sa.Column('sessions_note', sa.String(length=255), nullable=True))

    op.create_unique_constraint('uq_read_books_student_title_start', 'read_books', ['student_id', 'book_title', 'start_date'])

    # 3. Drop books table
    op.drop_table('books')


def downgrade():
    op.create_table(
        'books',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('book', sa.String(length=255), nullable=False),
        sa.Column('level', sa.String(length=20), nullable=False, server_default='0'),
        sa.Column('copies_note', sa.String(length=255), nullable=True),
        sa.Column('sessions_note', sa.String(length=255), nullable=True),
        sa.Column('disabled_at', sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint('id', name='books_pkey')
    )
    op.add_column('read_books', sa.Column('book_id', sa.Uuid(), nullable=True))
    op.create_foreign_key('read_books_book_id_fkey', 'read_books', 'books', ['book_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('uq_read_books_student_title_start', 'read_books', type_='unique')
    op.drop_column('read_books', 'sessions_note')
    op.drop_column('read_books', 'copies_note')
    op.drop_column('read_books', 'level')
    op.drop_column('read_books', 'book_title')
    op.create_unique_constraint('uq_read_books_student_book_start', 'read_books', ['student_id', 'book_id', 'start_date'])
