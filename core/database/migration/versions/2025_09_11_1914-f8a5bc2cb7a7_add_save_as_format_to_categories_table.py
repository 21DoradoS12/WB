"""add_save_as_format_to_categories_table

Revision ID: f8a5bc2cb7a7
Revises: 5865a902e3b1
Create Date: 2025-09-11 19:14:19.178921

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f8a5bc2cb7a7"
down_revision: Union[str, Sequence[str], None] = "5865a902e3b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("categories", sa.Column("save_as_format", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("categories", "save_as_format")
