"""Sync existing test results to read_books

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-09-28 02:45:00.000000

"""
from typing import Sequence, Union
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO read_books (id, student_id, test_id, start_date, end_date)
        SELECT
            uuidv7(),
            r.student_id,
            r.test_id,
            MIN(r.test_date),
            MAX(r.test_date)
        FROM results r
        LEFT JOIN read_books rb
            ON rb.student_id = r.student_id AND rb.test_id = r.test_id
        WHERE rb.id IS NULL
        GROUP BY r.student_id, r.test_id;
    """)


def downgrade() -> None:
    pass
