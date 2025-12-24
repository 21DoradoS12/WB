"""add name to tabble supplies

Revision ID: 5865a902e3b1
Revises: 7fa4bb2bb737
Create Date: 2025-09-05 00:21:00.254900

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5865a902e3b1"
down_revision: Union[str, Sequence[str], None] = "7fa4bb2bb737"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("supplies", sa.Column("name", sa.String(), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("supplies", "name")
