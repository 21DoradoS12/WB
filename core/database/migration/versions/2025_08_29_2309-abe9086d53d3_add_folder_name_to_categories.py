"""add folder name to categories

Revision ID: abe9086d53d3
Revises: ba2b9827d8ca
Create Date: 2025-08-29 23:09:06.166723

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "abe9086d53d3"
down_revision: Union[str, Sequence[str], None] = "ba2b9827d8ca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("categories", sa.Column("folder_name", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("categories", "folder_name")
