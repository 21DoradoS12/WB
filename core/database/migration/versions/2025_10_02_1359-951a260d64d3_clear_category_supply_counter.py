"""clear category_supply_counter

Revision ID: 951a260d64d3
Revises: f8a5bc2cb7a7
Create Date: 2025-10-02 13:59:57.712620

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "951a260d64d3"
down_revision: Union[str, Sequence[str], None] = "f8a5bc2cb7a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("DELETE FROM category_supply_counter")


def downgrade() -> None:
    """Downgrade schema."""
