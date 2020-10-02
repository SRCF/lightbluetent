from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from lightbluetent.config import PermissionType, RoleType
import enum

db = SQLAlchemy()
migrate = Migrate()

# Association table between users and groups.
user_group = db.Table(
    "users_groups",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("group_id", db.String(12), db.ForeignKey("groups.id"), primary_key=True),
)

# Association table between roles and permissions.
roles_permissions = db.Table(
    "roles_permissions",
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id"), primary_key=True),
    db.Column(
        "permission_id", db.Integer, db.ForeignKey("permissions.id"), primary_key=True
    ),
)

# Association table between attendees and either a group or a room.
# Groups may have a default whitelist, which can then be inherited by its rooms and modified if required.
whitelist = db.Table(
    "whitelist",
    db.Column("id", db.Integer, primary_key=True),
    db.Column("user_id", db.Integer, db.ForeignKey("users.id")),
    db.Column("group_id", db.String(12), db.ForeignKey("groups.id")),
    db.Column("room_id", db.String(20), db.ForeignKey("rooms.id")),
)

# Different levels of authentication for attendees joining a room
class Authentication(enum.Enum):
    PUBLIC = "public"
    RAVEN = "raven"
    PASSWORD = "password"
    WHITELIST = "whitelist"


class Recurrence(enum.Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKDAYS = "weekdays"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

class RecurrenceType(enum.Enum):
    FOREVER = "forever"
    UNTIL = "until"
    COUNT = "count"


class LinkType(enum.Enum):
    EMAIL = "email"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    OTHER = "other"

class Link(db.Model):
    __tablename__ = "links"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.String(16), db.ForeignKey("groups.id"), nullable=True)
    room_id = db.Column(db.String(16), db.ForeignKey("rooms.id"), nullable=True)
    url = db.Column(db.String, nullable=False)
    type = db.Column(db.Enum(LinkType), nullable=False, default=LinkType.OTHER)


class Room(db.Model):

    __tablename__ = "rooms"

    id = db.Column(
        db.String(20), primary_key=True
    )  # The room's meetingID: <group_id>-abc-def or <crsid>-abc-def

    name = db.Column(db.String(100), nullable=False)
    alias = db.Column(
        db.String(100), nullable=True, unique=True
    )  # e.g. "srcf-committee-meetings" corresponds to https://events.srcf.net/r/srcf-committee-meetings
    group_id = db.Column(
        db.String(12), db.ForeignKey("groups.id"), nullable=True
    )  # For group-owned rooms
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )  # For user-owned rooms
    sessions = db.relationship("Session", backref="room", lazy=True)
    links = db.relationship("Link", backref="room", lazy=True)
    description = db.Column(db.String, unique=False, nullable=True)

    welcome_text = db.Column(db.String, unique=False, nullable=True)
    banner_text = db.Column(db.String, unique=False, nullable=True)
    banner_color = db.Column(db.String, unique=False, nullable=True)
    mute_on_start = db.Column(db.Boolean, nullable=False, default=False)
    disable_private_chat = db.Column(db.Boolean, nullable=False, default=False)
    attendee_pw = db.Column(db.String, unique=True, nullable=False)
    moderator_pw = db.Column(db.String, unique=True, nullable=False)

    sessions = db.relationship("Session", backref="room", lazy=True)
    authentication = db.Column(
        db.Enum(Authentication), nullable=False, default=Authentication.PUBLIC
    )
    password = db.Column(db.String, nullable=True)

    whitelisted_users = db.relationship(
        "User",
        secondary=whitelist,
        lazy=True,
        backref=db.backref("rooms_whitelisted_for", lazy=True),
    )

    time_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Room(group: '{self.group}', name: '{self.name}')"


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    crsid = db.Column(db.String(7), db.CheckConstraint("crsid = lower(crsid)"))
    email = db.Column(db.String, unique=True, nullable=True)
    full_name = db.Column(db.String, unique=False, nullable=True)
    time_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)

    rooms = db.relationship("Room", backref="user", lazy=True)

    def has_permission_to(self, perm: PermissionType):
        return perm in [p.name for p in self.role.permissions]

    def __repr__(self):
        return f"User('{self.crsid}': '{self.full_name}', '{self.email}')"


class Group(db.Model):
    __tablename__ = "groups"

    id = db.Column(db.String(12), primary_key=True)  # e.g. "srcf"
    name = db.Column(
        db.String, unique=False, nullable=False
    )  # e.g. "Student-Run Computing Facility"
    owners = db.relationship(
        "User",
        secondary=user_group,
        lazy=True,
        backref=db.backref("groups", lazy=True),
    )
    rooms = db.relationship("Room", backref="group", lazy=True)

    whitelisted_users = db.relationship(
        "User",
        secondary=whitelist,
        lazy=True,
        backref=db.backref("groups_whitelisted_for", lazy=True),
    )

    description = db.Column(db.String, unique=False, nullable=True)
    links = db.relationship("Link", backref="group", lazy=True)

    logo = db.Column(
        db.String, unique=False, nullable=False, default="default_group_logo.png"
    )

    time_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Group('{self.name}')"


class Session(db.Model):
    __tablename__ = "sessions"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(16), db.ForeignKey("rooms.id"), nullable=True)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    recur = db.Column(db.Enum(Recurrence), nullable=False, default=Recurrence.NONE)
    count = db.Column(db.Integer, nullable=True)
    until = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"Session(group: '{self.group}', start: '{self.start}', end: '{self.end}', recur: '{self.recur}', limit: '{self.limit}')"


class Setting(db.Model):
    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=False, nullable=False)
    value = db.Column(db.String, unique=False, nullable=True)
    enabled = db.Column(db.Boolean, nullable=True, default=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Setting('{self.name}', '{self.enabled}')"


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.Enum(RoleType), unique=False, nullable=False)

    permissions = db.relationship(
        "Permission",
        secondary=roles_permissions,
        lazy=True,
        backref=db.backref("roles", lazy=True),
    )

    description = db.Column(db.String, unique=False, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    users = db.relationship("User", backref="role", lazy=True)

    def __repr__(self):
        return f"Role('{self.name}', '{self.description}')"


class Permission(db.Model):
    __tablename__ = "permissions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Enum(PermissionType), unique=False, nullable=False)

    def __repr__(self):
        return f"Permission('{self.name}')"
