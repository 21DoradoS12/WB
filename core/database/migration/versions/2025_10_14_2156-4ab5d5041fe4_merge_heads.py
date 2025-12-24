"""merge heads

Revision ID: 4ab5d5041fe4
Revises: d35c6909a3dd, 81937a940dbf
Create Date: 2025-10-14 21:56:47.275478

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "4ab5d5041fe4"
down_revision: Union[str, Sequence[str], None] = ("d35c6909a3dd", "81937a940dbf")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
