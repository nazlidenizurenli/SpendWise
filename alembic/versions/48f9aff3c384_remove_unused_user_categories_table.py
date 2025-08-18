"""remove unused user_categories table

Revision ID: 48f9aff3c384
Revises: afd38ff1669e
Create Date: 2025-08-17 14:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '48f9aff3c384'
down_revision: Union[str, Sequence[str], None] = 'afd38ff1669e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop the unused user_categories table."""
    # Drop the unique constraint first
    op.drop_constraint("uq_user_category", "user_categories", type_="unique")
    # Drop the table
    op.drop_table("user_categories")


def downgrade() -> None:
    """Recreate the user_categories table."""
    op.create_table(
        "user_categories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(length=64), nullable=False),
    )
    op.create_unique_constraint("uq_user_category", "user_categories", ["user_id", "name"])
