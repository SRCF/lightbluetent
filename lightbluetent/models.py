from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

db = SQLAlchemy()
migrate = Migrate()

# Association table for many-to-many relationship between admins and groups.
user_group = db.Table(
    "user_group",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column(
        "group_id", db.Integer, db.ForeignKey("groups.id"), primary_key=True
    ),
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
    # this needs to be made non nullable
    # TEMPFIX FOR EXISTING USERS!!!
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=True)

    # will it work if I use the backref here?
    def __repr__(self):
        return f"User('{self.crsid}': '{self.full_name}', '{self.email}')"


class Group(db.Model):
    __tablename__ = "groups"

    id = db.Column(db.Integer, primary_key=True)
    short_name = db.Column(db.String, unique=True, nullable=False)
    name = db.Column(db.String, unique=False, nullable=False)
    owners = db.relationship(
        "User",
        secondary=user_group,
        lazy=True,
        backref=db.backref("groups", lazy=True),
    )
    short_description = db.Column(db.String(200), unique=False, nullable=True)
    description = db.Column(db.String, unique=False, nullable=True)
    time_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # uid:    A short name for the group. Duplicate of short_name for now,
    #         but stored as lower case.
    # bbb_id: Randomly generated UUID. Sent to BBB as the meetingID parameter
    #         on the 'create' API call.

    website = db.Column(db.String, unique=False, nullable=True)
    socials = db.Column(db.JSON, nullable=False, default=list)
    sessions = db.Column(db.JSON, nullable=True, default=list)
    welcome_text = db.Column(db.String, unique=False, nullable=True)
    logo = db.Column(
        db.String, unique=False, nullable=False, default="default_logo.png"
    )
    bbb_logo = db.Column(
        db.String, unique=False, nullable=False, default="default_bbb_logo.png"
    )
    banner_text = db.Column(db.String, unique=False, nullable=True)
    banner_color = db.Column(db.String, unique=False, nullable=True, default="#e8e8e8")
    mute_on_start = db.Column(db.Boolean, nullable=False, default=False)
    disable_private_chat = db.Column(db.Boolean, nullable=False, default=False)
    attendee_pw = db.Column(db.String, unique=True, nullable=False)
    moderator_pw = db.Column(db.String, unique=True, nullable=False)
    uid = db.Column(db.String, unique=True, nullable=False)
    bbb_id = db.Column(db.String, unique=True, nullable=False)

    def __repr__(self):
        return f"Group('{self.name}', '{self.admins}')"


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
