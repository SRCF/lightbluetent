import pytest

from lightbluetent.app import create_app
from lightbluetent.models import db


@pytest.fixture
def app():
    app = create_app("testing")

    return app

# reset the database on each test to ensure reliability
@pytest.fixture(scope="function")
def database(app):
    with app.app_context():
        db.drop_all()
        db.create_all()

    yield db