"""user_categories table

Revision ID: afd38ff1669e
Revises: 5db90bdcac9f
Create Date: 2025-08-17 14:02:33.076491

"""
from typing import Sequence, Union
from sqlalchemy.dialects import postgresql
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'afd38ff1669e'
down_revision: Union[str, Sequence[str], None] = '5db90bdcac9f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "user_categories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(length=64), nullable=False),
    )
    op.create_unique_constraint("uq_user_category", "user_categories", ["user_id", "name"])

def downgrade():
    op.drop_constraint("uq_user_category", "user_categories", type_="unique")
    op.drop_table("user_categories")
