"""add added_to_supply_at to table wb_assembly_task

Revision ID: 7fa4bb2bb737
Revises: de578f5d006d
Create Date: 2025-09-04 23:08:50.987623

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7fa4bb2bb737"
down_revision: Union[str, Sequence[str], None] = "de578f5d006d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "wb_assembly_task",
        sa.Column("added_to_supply_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("wb_assembly_task", "added_to_supply_at")
