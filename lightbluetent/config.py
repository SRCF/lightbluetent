import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    """Base configuration"""

    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD")
    hostname = os.getenv("POSTGRES_HOSTNAME", "localhost")
    port = int(os.getenv("POSTGRES_PORT", 5432))
    database = os.getenv("APPLICATION_DB", "lightbluetent")
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_URI", f"postgresql+psycopg2://{user}:{password}@{hostname}:{port}/{database}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Requests up to 1 MB
    MAX_CONTENT_LENGTH = 1024 * 1024

    HAS_DIRECTORY_PAGE = True

class ProductionConfig(Config):
    """Production configuration"""


class DevelopmentConfig(Config):
    """Development configuration"""


class TestingConfig(Config):
    """Testing configuration"""

    TESTING = True
