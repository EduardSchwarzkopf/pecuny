"""add School material category

Revision ID: ebc9a4757806
Revises: 544b25e4c6f6
Create Date: 2024-03-10 18:24:28.589852

"""

from typing import Sequence, Union

from alembic import op
from app.data.categories import EDUCATION_ID
from app.models import TransactionCategory

# revision identifiers, used by Alembic.
revision: str = "ebc9a4757806"
down_revision: Union[str, None] = "544b25e4c6f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

table_name = TransactionCategory.__tablename__
category = "School material"
label = TransactionCategory.label.key


def upgrade() -> None:
    op.execute(
        f"INSERT INTO {table_name} ({label}, {TransactionCategory.section_id.key}) VALUES ('{category}', {EDUCATION_ID})"
    )


def downgrade() -> None:
    op.execute(f"DELETE FROM {table_name} WHERE {label} = '{category}'")
