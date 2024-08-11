"""add default value for is_active

Revision ID: dbce8a11ecc2
Revises: 3d95cdfbdd44
Create Date: 2024-06-23 09:21:50.927292

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "dbce8a11ecc2"
down_revision: Union[str, None] = "3d95cdfbdd44"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column(
        "transactions_scheduled", "is_active", server_default=sa.text("true")
    )
    op.execute("UPDATE transactions_scheduled SET is_active = true")


def downgrade():
    op.alter_column("transactions_scheduled", "is_active", server_default=None)
