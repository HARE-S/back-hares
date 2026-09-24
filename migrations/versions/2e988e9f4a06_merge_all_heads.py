"""merge_all_heads

Revision ID: 2e988e9f4a06
Revises: 008_align_sections_with_penascal, 25ed59d3b00b, 3f817b3bb9e1, b2c3d4e5f6a7
Create Date: 2026-09-24 08:05:22.881989

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e988e9f4a06'
down_revision: Union[str, Sequence[str], None] = ('008_align_sections_with_penascal', '25ed59d3b00b', '3f817b3bb9e1', 'b2c3d4e5f6a7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
