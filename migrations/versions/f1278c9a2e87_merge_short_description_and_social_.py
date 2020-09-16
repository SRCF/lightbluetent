"""Merge short_description and social media fields

Revision ID: f1278c9a2e87
Revises: 2c423286568f, 57ea5a7749e1
Create Date: 2020-09-16 15:44:51.580369

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1278c9a2e87'
down_revision = ('2c423286568f', '57ea5a7749e1')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
