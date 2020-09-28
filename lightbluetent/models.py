from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import enum

db = SQLAlchemy()
migrate = Migrate()

# Association table for many-to-many relationship between users and groups.
user_group = db.Table(
    "user_group",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column(
        "group_id", db.String(12), db.ForeignKey("groups.id"), primary_key=True
    ),
)

# Association table for many-to-many relationship between attendees and either a group or a room.
# Groups may have a default whitelist, which can then be inherited by its rooms and modified if required.
whitelist = db.Table(
    "whitelist",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("group_id", db.String(12), db.ForeignKey("groups.id")),
    db.Column("room_id", db.String(12), db.ForeignKey("rooms.id"))
)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    crsid = db.Column(db.String(7), db.CheckConstraint("crsid = lower(crsid)"))
    email = db.Column(db.String, unique=True, nullable=False)
    full_name = db.Column(db.String, unique=False, nullable=False)
    first_name = db.Column(db.String, unique=False, nullable=True)
    surname = db.Column(db.String, unique=False, nullable=True)
    time_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)


    def __repr__(self):
        return f"User('{self.crsid}': '{self.full_name}', '{self.email}')"


class Group(db.Model):
    __tablename__ = "groups"

    id = db.Column(db.String(12), primary_key=True)             # e.g. "srcf"
    name = db.Column(db.String, unique=False, nullable=False)   # e.g. "Student-Run Computing Facility"
    owners = db.relationship(
        "User",
        secondary=user_group,
        lazy=True,
        backref=db.backref("groups", lazy=True),
    )

    whitelisted_users = db.relationship(
        "User",
        secondary=whitelist,
        lazy=True,
        backref=db.backref("groups_whitelisted_for", lazy=True)
    )

    short_description = db.Column(db.String(200), unique=False, nullable=True)
    description = db.Column(db.String, unique=False, nullable=True)
    links = db.relationship('Link', backref="group", lazy=True)

    logo = db.Column(
        db.String, unique=False, nullable=False, default="default_logo.png"
    )

    time_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Group('{self.name}')"

# Different levels of authentication for attendees joining a room
class Authentication(enum.Enum):
    PUBLIC = 1
    RAVEN = 2
    PASSWORD = 3
    WHITELIST = 4

class Room(db.Model):

    __tablename__ = "rooms"

    id = db.Column(db.String(12), primary_key=True)       # The room's meetingID

    name = db.Column(db.String(100), nullable=False)
    group_id = db.Column(db.String(12), db.ForeignKey('groups.id'), nullable=False)
    sessions = db.relationship('Session', backref='room', lazy=True)
    links = db.relationship('Link', backref="room", lazy=True)

    welcome_text = db.Column(db.String, unique=False, nullable=True)
    banner_text = db.Column(db.String, unique=False, nullable=True)
    banner_color = db.Column(db.String, unique=False, nullable=True, default="#e8e8e8")
    mute_on_start = db.Column(db.Boolean, nullable=False, default=False)
    disable_private_chat = db.Column(db.Boolean, nullable=False, default=False)
    attendee_pw = db.Column(db.String, unique=True, nullable=False)
    moderator_pw = db.Column(db.String, unique=True, nullable=False)

    sessions = db.relationship("Session", backref="room", lazy=True)
    authentication = db.Column(db.Enum(Authentication), nullable=False, default=Authentication.PUBLIC)

    logo = db.Column(
        db.String, unique=False, nullable=False, default="default_room_logo.png"
    )

    whitelisted_users = db.relationship(
        "User",
        secondary=whitelist,
        lazy=True,
        backref=db.backref("rooms_whitelisted_for", lazy=True)
    )

    time_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Room(group: '{self.group}', name: '{self.name}')"


class Recurrence(enum.Enum):
    NONE = 1
    DAILY = 2
    WEEKDAYS = 3
    WEEKLY = 4
    MONTHLY = 5
    YEARLY = 6

class RecurrenceLimit(enum.Enum):
    FOREVER = 1   # No limit is given
    COUNT = 2     # A number of days / weeks months to recur is provided
    UNTIL = 3     # A date is given after which no more sessions will occur

class Session(db.Model):
    __tablename__ = "sessions"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(16), db.ForeignKey("rooms.id"), nullable=True)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    recur = db.Column(db.Enum(Recurrence), nullable=False, default=Recurrence.NONE)
    limit = db.Column(db.Enum(RecurrenceLimit), nullable=True)

    def __repr__(self):
        return f"Session(group: '{self.group}', start: '{self.start}', end: '{self.end}', reccur: '{self.recur}', limit: '{self.limit}')"


class LinkType(enum.Enum):
    EMAIL = 1
    FACEBOOK = 2
    TWITTER = 3
    INSTAGRAM = 4
    YOUTUBE = 5
    OTHER = 6

class Link(db.Model):
    __tablename__ = "links"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.String(16), db.ForeignKey("groups.id"), nullable=True)
    room_id = db.Column(db.String(16), db.ForeignKey("rooms.id"), nullable=True)
    url = db.Column(db.String, nullable=False)
    type = db.Column(db.Enum(LinkType), nullable=False, default=LinkType.OTHER)


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
    name = db.Column(db.String, unique=False, nullable=False)
    permission_id = db.Column(
        db.Integer, db.ForeignKey("permissions.id"), nullable=False
    )
    description = db.Column(db.String, unique=False, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    users = db.relationship("User", backref="role", lazy=True)

    def __repr__(self):
        return f"Role('{self.name}', '{self.description}')"


class Permission(db.Model):
    __tablename__ = "permissions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=False, nullable=False)
    roles = db.relationship("Role", backref="permission", lazy=True)

    def __repr__(self):
        return f"Permission('{self.name}')"
