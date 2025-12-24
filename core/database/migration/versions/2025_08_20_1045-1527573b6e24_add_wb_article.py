"""add wb article

Revision ID: 1527573b6e24
Revises: d7f8513d5278
Create Date: 2025-08-20 10:45:18.487087

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1527573b6e24"
down_revision: Union[str, Sequence[str], None] = "d7f8513d5278"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "wb_articles",
        sa.Column("wb_article", sa.Integer(), nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.ForeignKeyConstraint(
            ["template_id"],
            ["templates.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("wb_articles")
