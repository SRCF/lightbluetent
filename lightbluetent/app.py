from flask import Flask


def create_app(config_name):

    app = Flask(__name__)

    config_module = f"lightbluetent.config.{config_name.capitalize()}Config"

    app.config.from_object(config_module)
 
    from lightbluetent.models import db, migrate

    db.init_app(app)
    migrate.init_app(app, db)

    @app.route("/")
    def hello_world():
        return "Hello, World!"

    return app