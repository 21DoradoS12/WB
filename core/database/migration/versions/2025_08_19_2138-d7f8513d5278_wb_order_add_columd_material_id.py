"""wb_order add columd material_id

Revision ID: d7f8513d5278
Revises: ced038bd7904
Create Date: 2025-08-19 21:38:45.015263

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d7f8513d5278"
down_revision: Union[str, Sequence[str], None] = "ced038bd7904"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("wb_orders", sa.Column("material_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        None, "wb_orders", "materials", ["material_id"], ["id"], ondelete="CASCADE"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(None, "wb_orders", type_="foreignkey")
    op.drop_column("wb_orders", "material_id")
