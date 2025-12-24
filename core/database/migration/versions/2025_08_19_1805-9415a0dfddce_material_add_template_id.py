"""material add template_id

Revision ID: 9415a0dfddce
Revises: 2b7fd3671c59
Create Date: 2025-08-19 18:05:33.234134

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9415a0dfddce"
down_revision: Union[str, Sequence[str], None] = "2b7fd3671c59"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("materials", sa.Column("user_id", sa.BigInteger(), nullable=False))
    op.add_column("materials", sa.Column("template_id", sa.Integer(), nullable=False))
    op.create_foreign_key(
        None, "materials", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        None, "materials", "templates", ["template_id"], ["id"], ondelete="CASCADE"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(None, "materials", type_="foreignkey")
    op.drop_constraint(None, "materials", type_="foreignkey")
    op.drop_column("materials", "template_id")
    op.drop_column("materials", "user_id")
