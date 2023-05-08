"""add frequency data

Revision ID: 1ff68f765c15
Revises: bca3fd7e27dd
Create Date: 2023-01-04 06:33:58.671369

"""
from alembic import op
import sqlalchemy as sa
from app.data.frequencies import get_frequency_list
from app import models


# revision identifiers, used by Alembic.
revision = "1ff68f765c15"
down_revision = "bca3fd7e27dd"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)

    def create_category_model(frequency: dict):
        return models.Frequency(**frequency)

    frequency_list = list(map(create_category_model, get_frequency_list()))

    session.add_all(frequency_list)
    session.commit()


def downgrade():
    pass
