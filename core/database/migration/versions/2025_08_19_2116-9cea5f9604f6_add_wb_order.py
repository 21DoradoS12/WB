"""add wb_order

Revision ID: 9cea5f9604f6
Revises: 9164e3d907fc
Create Date: 2025-08-19 21:16:56.328693

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9cea5f9604f6"
down_revision: Union[str, Sequence[str], None] = "9164e3d907fc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "wb_orders",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("region_name", sa.String(), nullable=False),
        sa.Column("supplier_article", sa.String(), nullable=False),
        sa.Column("country_name", sa.String(), nullable=False),
        sa.Column("nm_id", sa.BigInteger(), nullable=False),
        sa.Column("is_cancel", sa.Boolean(), nullable=False),
        sa.Column("warehouse_name", sa.String(), nullable=True),
        sa.Column("warehouse_type", sa.String(), nullable=True),
        sa.Column("cancel_date", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("wb_orders")
