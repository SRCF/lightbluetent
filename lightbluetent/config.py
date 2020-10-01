import os
import enum


basedir = os.path.abspath(os.path.dirname(__file__))

class PermissionType(enum.Enum):
    CAN_VIEW_ADMIN_PAGE = "can_view_admin_page"                 # Admins
    CAN_MANAGE_ALL_GROUPS = "can_manage_all_groups"             # Admins
    CAN_MANAGE_ALL_ROOMS = "can_manage_all_rooms"               # Admins
    CAN_START_ALL_ROOMS = "can_start_all_rooms"                 # Admins
    CAN_DELETE_ALL_ROOMS = "can_delete_all_rooms"               # Admins
    CAN_CREATE_OWN_ROOMS = "can_create_own_rooms"               # Users
    CAN_DELETE_OWN_ROOMS = "can_delete_own_rooms"               # Users
    CAN_MANAGE_OWN_ROOMS = "can_manage_own_rooms"               # Users
    CAN_START_OWN_ROOMS = "can_start_rooms"                     # Users
    CAN_JOIN_WHITELISTED_ROOMS = "can_join_whitelisted_rooms"   # Visitors

class RoleType(enum.Enum):
    VISITOR = "visitor"
    USER = "user"
    ADMINISTRATOR = "administrator"

class Config(object):
    """Base configuration"""

    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD")
    hostname = os.getenv("POSTGRES_HOSTNAME", "localhost")
    port = int(os.getenv("POSTGRES_PORT", 5432))
    database = os.getenv("APPLICATION_DB", "lightbluetent")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "SQLALCHEMY_URI",
        f"postgresql+psycopg2://{user}:{password}@{hostname}:{port}/{database}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Requests up to 1 MB
    MAX_CONTENT_LENGTH = 1024 * 1024

    HAS_DIRECTORY_PAGE = False
    NUMBER_OF_DAYS = 2

    DEFAULT_GROUP_LOGO = "default_group_logo.png"
    DEFAULT_ROOM_LOGO = "default_room_logo.png"
    MAX_LOGO_SIZE = (512, 512)
    LOGO_ALLOWED_EXTENSIONS = {".png", ".jpeg", ".jpg", ".gif"}
    IMAGES_DIR = "lightbluetent/static/images"

    # Since using url_for(static", ...) prepends lightbluetent/static to the URL
    # for us, we have the relative path to the images directory from the static folder.
    # I couldn't think of a better way of doing this. Required in groups.py for
    # getting the URL of the bbb_logo to pass to BBB.
    IMAGES_DIR_FROM_STATIC = "images"


    # defines the default roles that come with the app
    # a role has permissions associated with it
    ROLES_INFO = []

    visitor_permissions = [
        PermissionType.CAN_JOIN_WHITELISTED_ROOMS
    ]

    ROLES_INFO.append(
        {
            "role": RoleType.VISITOR,
            "permissions": visitor_permissions,
            "description": "A visitor can join rooms",
        }
    )

    user_permissions = visitor_permissions + [
        PermissionType.CAN_CREATE_OWN_ROOMS,
        PermissionType.CAN_DELETE_OWN_ROOMS,
        PermissionType.CAN_MANAGE_OWN_ROOMS,
        PermissionType.CAN_START_OWN_ROOMS
    ]

    ROLES_INFO.append(
        {
            "role": RoleType.USER,
            "permissions": user_permissions,
            "description": "A user can create rooms",
        }
    )

    admin_permissions = user_permissions + [
        PermissionType.CAN_VIEW_ADMIN_PAGE,
        PermissionType.CAN_MANAGE_ALL_GROUPS,
        PermissionType.CAN_MANAGE_ALL_ROOMS,
        PermissionType.CAN_START_ALL_ROOMS,
        PermissionType.CAN_DELETE_ALL_ROOMS
    ]

    ROLES_INFO.append(
        {
            "role": RoleType.ADMINISTRATOR,
            "permissions": admin_permissions,
            "description": "An administrator can manage site settings and room features for LightBlueTent",
        }
    )

    SITE_SETTINGS = []
    SITE_SETTINGS.append(
        {"name": "enable_signups", "enabled": os.getenv("ENABLE_SIGNUPS", True)}
    )
    SITE_SETTINGS.append(
        {
            "name": "enable_room_creation",
            "enabled": os.getenv("ENABLE_ROOM_CREATION", True),
        }
    )


class ProductionConfig(Config):
    """Production configuration"""


class DevelopmentConfig(Config):
    """Development configuration"""


class TestingConfig(Config):
    """Testing configuration"""

    TESTING = True
