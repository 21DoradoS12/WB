"""add wb_assembly_task

Revision ID: ced038bd7904
Revises: 9cea5f9604f6
Create Date: 2025-08-19 21:31:40.345548

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ced038bd7904"
down_revision: Union[str, Sequence[str], None] = "9cea5f9604f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "wb_assembly_task",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("wb_order_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["wb_order_id"],
            ["wb_orders.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("wb_assembly_task")
