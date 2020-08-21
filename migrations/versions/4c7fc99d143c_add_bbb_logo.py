"""Add bbb_logo

Revision ID: 4c7fc99d143c
Revises: 74021af9ca81
Create Date: 2020-08-21 13:56:29.869486

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4c7fc99d143c'
down_revision = '74021af9ca81'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('societies', sa.Column('bbb_logo', sa.String(), nullable=False))
    op.alter_column('societies', 'logo',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.create_unique_constraint(None, 'societies', ['logo'])
    op.create_unique_constraint(None, 'societies', ['bbb_logo'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'societies', type_='unique')
    op.drop_constraint(None, 'societies', type_='unique')
    op.alter_column('societies', 'logo',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.drop_column('societies', 'bbb_logo')
    # ### end Alembic commands ###
