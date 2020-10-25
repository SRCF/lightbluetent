from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from flask_migrate import Migrate
from datetime import datetime
from lightbluetent.config import PermissionType, RoleType
from flask import current_app
import enum

db = SQLAlchemy()
migrate = Migrate()


# Association table between users and groups.
user_group = db.Table(
    "users_groups",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("group_id", db.String(20), db.ForeignKey("groups.id"), primary_key=True),
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
    db.Column("group_id", db.String(20), db.ForeignKey("groups.id")),
    db.Column("room_id", db.String(28), db.ForeignKey("rooms.id")),
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
    group_id = db.Column(db.String(20), db.ForeignKey("groups.id"), nullable=True)
    room_id = db.Column(db.String(28), db.ForeignKey("rooms.id"), nullable=True)
    name = db.Column(db.String, nullable=True)
    url = db.Column(db.String, nullable=True)
    display_order = db.Column(db.Integer, nullable=False)
    type = db.Column(db.Enum(LinkType), nullable=False, default=LinkType.OTHER)

    def __repr__(self):
        return f"Link(room: {self.room!r}, name: {self.name!r}, url: {self.url!r})"


class Room(db.Model):

    __tablename__ = "rooms"

    id = db.Column(
        db.String(28), primary_key=True
    )  # The room's meetingID: <group_id>-abc-def or <crsid>-abc-def

    name = db.Column(db.String(100), nullable=False)
    alias = db.Column(
        db.String(100), nullable=True, unique=True
    )  # e.g. "srcf-committee-meetings" corresponds to https://events.srcf.net/r/srcf-committee-meetings
    group_id = db.Column(
        db.String(20), db.ForeignKey("groups.id"), nullable=True
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
    force_listen_only = db.Column(db.Boolean, nullable=False, default=False)
    cameras_moderator_only = db.Column(db.Boolean, nullable=False, default=False)
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
        return f"Room(group: {self.group!r}, name: {self.name!r})"

    def get_next_link(self):
        # have we already created an empty link?
        # add default for when self.links is empty
        next_link = next((link for link in self.links if not link.url), False)
        # if not, let's create one
        if next_link:
            return next_link
        else:
            # make sure that we preserve link order
            sorted_links = self.preserve_display_order()
            next_order = sorted_links[-1].display_order + 1 if sorted_links else 0
            new_link = Link(display_order=next_order)
            self.links.append(new_link)
            db.session.commit()
            current_app.logger.info(f"Created empty link: {new_link}")
            return new_link

    def get_display_order(self):
        out = [0] * len(self.links)
        for link in self.links:
            out[link.display_order] = str(link.id)
        return "|".join(out)


    def preserve_display_order(self):
        sorted_links = (
            Link.query.filter_by(room_id=self.id)
            .order_by(Link.display_order.asc())
            .all()
        )
        for order, link in enumerate(sorted_links):
            link.display_order = order
        return sorted_links


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
        return f"User({self.crsid!r}: {self.full_name!r}, {self.email!r})"


class Group(db.Model):
    __tablename__ = "groups"

    id = db.Column(db.String(20), primary_key=True)  # e.g. "srcf"
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

    logo = db.Column(db.String, unique=False, nullable=True)

    time_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Group({self.name!r})"

    def get_display_order(self):
        out = [0] * len(self.links)
        for link in self.links:
            out[link.display_order] = str(link.id)
        return "|".join(out)

    def preserve_display_order(self):
        sorted_links = (
            Link.query.filter_by(group_id=self.id)
            .order_by(Link.display_order.asc())
            .all()
        )
        for order, link in enumerate(sorted_links):
            link.display_order = order
        return sorted_links

    def get_next_link(self):
        # have we already created an empty link?
        # add default for when self.links is empty
        next_link = next((link for link in self.links if not link.url), False)
        # if not, let's create one
        if next_link:
            return next_link
        else:
            # make sure that we preserve link order
            sorted_links = self.preserve_display_order()
            next_order = sorted_links[-1].display_order + 1 if sorted_links else 0
            new_link = Link(display_order=next_order)
            self.links.append(new_link)
            db.session.commit()
            current_app.logger.info(f"Created empty link: {new_link}")
            return new_link

    def delete_logo(self):
        images_dir = current_app.config["IMAGES_DIR"]
        if not os.path.isdir(images_dir):
            current_app.logger.info(f"'{ images_dir }':  no such directory.")
            return False

        if self.logo is None:
            return True

        current_app.logger.info(f"For id='{ self.id }': deleting logo...")
        for asset in Asset.query.filter_by(key=self.logo):
            old_logo = os.path.join(images_dir, asset.path)
            delete_logo_variant(old_logo)
            db.session.delete(asset)
        self.logo = None
        db.session.commit()
        return True


class Session(db.Model):
    __tablename__ = "sessions"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(28), db.ForeignKey("rooms.id"), nullable=True)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    recur = db.Column(db.Enum(Recurrence), nullable=False, default=Recurrence.NONE)
    count = db.Column(db.Integer, nullable=True)
    until = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"Session(group: {self.group!r}, start: {self.start!r}, end: {self.end!r}, reccur: {self.recur!r}, limit: {self.limit!r})"


class Setting(db.Model):
    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=False, nullable=False)
    value = db.Column(db.String, unique=False, nullable=True)
    enabled = db.Column(db.Boolean, nullable=True, default=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Setting({self.name!r}, {self.enabled!r})"


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
        return f"Role({self.name!r}, {self.description!r})"


class Permission(db.Model):
    __tablename__ = "permissions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Enum(PermissionType), unique=False, nullable=False)

    def __repr__(self):
        return f"Permission({self.name!r})"


class Asset(db.Model):
    """
    The asset table allows storage of assets, but crucially, allows
    asset variants to be defined. For example, for image assets one may
    have HiDPI variants for @1x, @2x, etc; this would be stored as:

        id | key       | variant | path
        ---|-----------|---------|-------------------------
         1 | srcf-logo | @1x     | srcf-logo-19a6c2c9.png
         2 | foo-logo  | NULL    | foo-bar.jpeg
         3 | srcf-logo | @2x     | srcf-logo-35d372d5.png
        ...

    """

    __tablename__ = "assets"
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String, unique=False, nullable=False)
    variant = db.Column(db.String, unique=False, nullable=True)
    path = db.Column(db.String, unique=True, nullable=False)

    def __repr__(self):
        if self.variant is None:
            return f"Asset({self.key!r}: {self.path!r})"
        return f"Asset({self.key!r}/{self.variant!r}: {self.path!r})"


# @event.listens_for(Link, "after_insert")
# @event.listens_for(Link, "after_delete")
# def preserve_display_order(mapper, conn, target):
#     sorted_links = None
#     link_table = Link.__table__
#     if target.group:
#         sorted_links = (
#             Link.query.filter_by(group_id=target.group.id)
#             .order_by(Link.display_order.asc())
#             .all()
#         )
#     elif target.room:
#         sorted_links = (
#             Link.query.filter_by(room_id=target.room.id)
#             .order_by(Link.display_order.asc())
#             .all()
#         )
#     for order, link in enumerate(sorted_links):
#         link.display_order = order
#     conn.execute(
#         link_table.update().
#         where(link_table.c.id==target.id).

#     )

