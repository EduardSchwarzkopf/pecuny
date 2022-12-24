"""add categories and sections

Revision ID: bca3fd7e27dd
Revises: dc4328c6f608
Create Date: 2022-12-24 07:37:32.643941

"""
from alembic import op
import sqlalchemy as sa
from app.data import categories
from app import models

# revision identifiers, used by Alembic.
revision = "bca3fd7e27dd"
down_revision = "dc4328c6f608"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)
    section_list = categories.get_section_list()
    category_list = categories.get_category_list()

    def create_section_model(section):
        return models.TransactionSection(**section)

    def create_category_model(category):
        return models.TransactionCategory(**category)

    section = list(map(create_section_model, section_list))
    category = list(map(create_category_model, category_list))

    session.add_all(section + category)
    session.commit()


def downgrade():
    pass
