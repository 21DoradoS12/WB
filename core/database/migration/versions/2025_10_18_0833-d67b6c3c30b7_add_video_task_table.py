"""add video task table

Revision ID: d67b6c3c30b7
Revises: 5183115df39c
Create Date: 2025-10-18 08:33:11.172797

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d67b6c3c30b7"
down_revision: Union[str, Sequence[str], None] = "5183115df39c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "video_tasks",
        sa.Column("params", sa.JSON(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "processing", "done", "error", name="videostatus"),
            nullable=False,
        ),
        sa.Column("result_path", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
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
    op.drop_table("video_tasks")
