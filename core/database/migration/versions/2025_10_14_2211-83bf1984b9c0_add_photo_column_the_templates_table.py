"""add photo column the templates table

Revision ID: 83bf1984b9c0
Revises: 4ab5d5041fe4
Create Date: 2025-10-14 22:11:14.815384

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "83bf1984b9c0"
down_revision: Union[str, Sequence[str], None] = "4ab5d5041fe4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("templates", sa.Column("photo", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("templates", "photo")
