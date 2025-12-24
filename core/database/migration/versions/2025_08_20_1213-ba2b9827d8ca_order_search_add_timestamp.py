"""order_search add timestamp

Revision ID: ba2b9827d8ca
Revises: 1527573b6e24
Create Date: 2025-08-20 12:13:51.180715

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ba2b9827d8ca"
down_revision: Union[str, Sequence[str], None] = "1527573b6e24"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "order_search",
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
    )
    op.add_column(
        "order_search",
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("order_search", "updated_at")
    op.drop_column("order_search", "created_at")
