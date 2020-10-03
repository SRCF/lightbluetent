"""First migration

Revision ID: b9f807f35e93
Revises: 
Create Date: 2020-10-03 16:42:54.781992

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b9f807f35e93'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('assets',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('key', sa.String(), nullable=False),
    sa.Column('variant', sa.String(), nullable=True),
    sa.Column('path', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('path')
    )
    op.create_table('groups',
    sa.Column('id', sa.String(length=12), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('logo', sa.String(), nullable=True),
    sa.Column('time_created', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('permissions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Enum('CAN_VIEW_ADMIN_PAGE', 'CAN_MANAGE_ALL_GROUPS', 'CAN_MANAGE_ALL_ROOMS', 'CAN_START_ALL_ROOMS', 'CAN_DELETE_ALL_ROOMS', 'CAN_CREATE_OWN_ROOMS', 'CAN_DELETE_OWN_ROOMS', 'CAN_MANAGE_OWN_ROOMS', 'CAN_START_OWN_ROOMS', 'CAN_JOIN_WHITELISTED_ROOMS', name='permissiontype'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('roles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('role', sa.Enum('VISITOR', 'USER', 'ADMINISTRATOR', name='roletype'), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
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
    op.create_table('roles_permissions',
    sa.Column('role_id', sa.Integer(), nullable=False),
    sa.Column('permission_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
    sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('crsid', sa.String(length=7), nullable=True),
    sa.Column('email', sa.String(), nullable=True),
    sa.Column('full_name', sa.String(), nullable=True),
    sa.Column('time_created', sa.DateTime(), nullable=False),
    sa.Column('role_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('rooms',
    sa.Column('id', sa.String(length=20), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('alias', sa.String(length=100), nullable=True),
    sa.Column('group_id', sa.String(length=12), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('links_order', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('welcome_text', sa.String(), nullable=True),
    sa.Column('banner_text', sa.String(), nullable=True),
    sa.Column('banner_color', sa.String(), nullable=True),
    sa.Column('mute_on_start', sa.Boolean(), nullable=False),
    sa.Column('disable_private_chat', sa.Boolean(), nullable=False),
    sa.Column('attendee_pw', sa.String(), nullable=False),
    sa.Column('moderator_pw', sa.String(), nullable=False),
    sa.Column('authentication', sa.Enum('PUBLIC', 'RAVEN', 'PASSWORD', 'WHITELIST', name='authentication'), nullable=False),
    sa.Column('password', sa.String(), nullable=True),
    sa.Column('time_created', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('alias'),
    sa.UniqueConstraint('attendee_pw'),
    sa.UniqueConstraint('moderator_pw')
    )
    op.create_table('users_groups',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('group_id', sa.String(length=12), nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'group_id')
    )
    op.create_table('links',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('group_id', sa.String(length=16), nullable=True),
    sa.Column('room_id', sa.String(length=16), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('url', sa.String(), nullable=True),
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
    sa.Column('recur', sa.Enum('NONE', 'DAILY', 'WEEKDAYS', 'WEEKLY', name='recurrence'), nullable=False),
    sa.Column('count', sa.Integer(), nullable=True),
    sa.Column('until', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('whitelist',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('group_id', sa.String(length=12), nullable=True),
    sa.Column('room_id', sa.String(length=20), nullable=True),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
    sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('whitelist')
    op.drop_table('sessions')
    op.drop_table('links')
    op.drop_table('users_groups')
    op.drop_table('rooms')
    op.drop_table('users')
    op.drop_table('roles_permissions')
    op.drop_table('settings')
    op.drop_table('roles')
    op.drop_table('permissions')
    op.drop_table('groups')
    op.drop_table('assets')
    # ### end Alembic commands ###