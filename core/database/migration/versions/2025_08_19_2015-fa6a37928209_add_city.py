"""add city

Revision ID: fa6a37928209
Revises: 52b8306cc6bd
Create Date: 2025-08-19 20:15:09.615689

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fa6a37928209"
down_revision: Union[str, Sequence[str], None] = "52b8306cc6bd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "city",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("country_id", sa.Integer(), nullable=False),
        sa.Column("region", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("utc_offset", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["country_id"],
            ["country.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("city")
