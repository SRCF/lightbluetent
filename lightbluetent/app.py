from flask import Flask
from . import admin, home


def create_app(config_name):

    app = Flask(__name__,
                template_folder="templates")

    config_module = f"lightbluetent.config.{config_name.capitalize()}Config"

    app.config.from_object(config_module)
 
    from lightbluetent.models import db, migrate

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(admin.bp)
    app.register_blueprint(home.bp)

    return app
