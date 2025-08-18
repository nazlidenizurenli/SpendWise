"""rename budget amount to limit

Revision ID: 0fe176d690c4
Revises: 48f9aff3c384
Create Date: 2025-08-17 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0fe176d690c4'
down_revision: Union[str, Sequence[str], None] = '48f9aff3c384'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename amount column to limit in budgets table."""
    # Rename the column from 'amount' to 'limit'
    op.alter_column('budgets', 'amount', new_column_name='limit')


def downgrade() -> None:
    """Rename limit column back to amount in budgets table."""
    # Rename the column back from 'limit' to 'amount'
    op.alter_column('budgets', 'limit', new_column_name='amount')
