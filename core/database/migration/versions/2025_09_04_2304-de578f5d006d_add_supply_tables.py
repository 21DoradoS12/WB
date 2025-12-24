"""add_supply tables

Revision ID: de578f5d006d
Revises: abe9086d53d3
Create Date: 2025-09-04 23:04:13.830208

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "de578f5d006d"
down_revision: Union[str, Sequence[str], None] = "abe9086d53d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "category_supply_counter",
        sa.Column("category_name", sa.String(), nullable=False),
        sa.Column("supply_count", sa.Integer(), nullable=False),
        sa.Column(
            "date", sa.Date(), server_default=sa.text("CURRENT_DATE"), nullable=False
        ),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "supplies",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("category_name", sa.String(), nullable=False),
        sa.Column("order_count", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.add_column(
        "wb_assembly_task", sa.Column("supply_id", sa.String(), nullable=True)
    )
    op.create_foreign_key(
        None, "wb_assembly_task", "supplies", ["supply_id"], ["id"], ondelete="CASCADE"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(None, "wb_assembly_task", type_="foreignkey")
    op.drop_column("wb_assembly_task", "supply_id")
    op.drop_table("supplies")
    op.drop_table("category_supply_counter")
