"""Initial migration

Revision ID: 48e75b77cac1
Revises: 
Create Date: 2020-09-29 20:43:52.754299

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '48e75b77cac1'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('groups',
    sa.Column('id', sa.String(length=12), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('logo', sa.String(), nullable=False),
    sa.Column('time_created', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('permissions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('settings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('value', sa.String(), nullable=True),
    sa.Column('enabled', sa.Boolean(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('roles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('permission_id', sa.Integer(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('rooms',
    sa.Column('id', sa.String(length=12), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('alias', sa.String(length=100), nullable=True),
    sa.Column('group_id', sa.String(length=12), nullable=False),
    sa.Column('welcome_text', sa.String(), nullable=True),
    sa.Column('banner_text', sa.String(), nullable=True),
    sa.Column('banner_color', sa.String(), nullable=True),
    sa.Column('mute_on_start', sa.Boolean(), nullable=False),
    sa.Column('disable_private_chat', sa.Boolean(), nullable=False),
    sa.Column('attendee_pw', sa.String(), nullable=False),
    sa.Column('moderator_pw', sa.String(), nullable=False),
    sa.Column('authentication', sa.Enum('PUBLIC', 'RAVEN', 'PASSWORD', 'WHITELIST', name='authentication'), nullable=False),
    sa.Column('time_created', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('alias'),
    sa.UniqueConstraint('attendee_pw'),
    sa.UniqueConstraint('moderator_pw')
    )
    op.create_table('links',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('group_id', sa.String(length=16), nullable=True),
    sa.Column('room_id', sa.String(length=16), nullable=True),
    sa.Column('url', sa.String(), nullable=False),
    sa.Column('type', sa.Enum('EMAIL', 'FACEBOOK', 'TWITTER', 'INSTAGRAM', 'YOUTUBE', 'OTHER', name='linktype'), nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
    sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('sessions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('room_id', sa.String(length=16), nullable=True),
    sa.Column('start', sa.DateTime(), nullable=False),
    sa.Column('end', sa.DateTime(), nullable=False),
    sa.Column('recur', sa.Enum('NONE', 'DAILY', 'WEEKDAYS', 'WEEKLY', 'MONTHLY', 'YEARLY', name='recurrence'), nullable=False),
    sa.Column('limit', sa.Enum('FOREVER', 'COUNT', 'UNTIL', name='recurrencelimit'), nullable=True),
    sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('crsid', sa.String(length=7), nullable=True),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('full_name', sa.String(), nullable=False),
    sa.Column('first_name', sa.String(), nullable=True),
    sa.Column('surname', sa.String(), nullable=True),
    sa.Column('time_created', sa.DateTime(), nullable=False),
    sa.Column('role_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('user_group',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('group_id', sa.String(length=12), nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'group_id')
    )
    op.create_table('whitelist',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('group_id', sa.String(length=12), nullable=True),
    sa.Column('room_id', sa.String(length=12), nullable=True),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
    sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('user_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('whitelist')
    op.drop_table('user_group')
    op.drop_table('users')
    op.drop_table('sessions')
    op.drop_table('links')
    op.drop_table('rooms')
    op.drop_table('roles')
    op.drop_table('settings')
    op.drop_table('permissions')
    op.drop_table('groups')
    # ### end Alembic commands ###
