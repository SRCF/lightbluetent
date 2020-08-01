import os
from flask import Flask
from . import admin, home


def create_app(config_name):

    app = Flask(__name__,
                template_folder="templates")

    config_module = f"lightbluetent.config.{config_name.capitalize()}Config"

    app.config.from_object(config_module)

    if not app.secret_key and 'FLASK_SECRET_KEY' in os.environ:
        app.secret_key = os.environ['FLASK_SECRET_KEY']

    if not app.request_class.trusted_hosts and 'FLASK_TRUSTED_HOSTS' in os.environ:
        app.request_class.trusted_hosts = os.environ['FLASK_TRUSTED_HOSTS'].split(",")

    from lightbluetent.models import db, migrate

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(admin.bp)
    app.register_blueprint(home.bp)

    return app
