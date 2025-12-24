"""add order search

Revision ID: 9164e3d907fc
Revises: fa6a37928209
Create Date: 2025-08-19 20:39:12.188619

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9164e3d907fc"
down_revision: Union[str, Sequence[str], None] = "fa6a37928209"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "order_search",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("material_id", sa.Integer(), nullable=False),
        sa.Column("search_type", sa.String(), nullable=False),
        sa.Column("filters", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column(
            "last_checked_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["material_id"],
            ["materials.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("order_search")
