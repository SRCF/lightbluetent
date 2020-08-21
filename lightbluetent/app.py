import os
from flask import Flask
from . import admin, home, society

def create_app(config_name=None):

    if config_name == None:
        config_name = "Production"

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
    app.register_blueprint(society.bp)

    @app.context_processor
    def inject_gh_rev():
        return dict(github_rev=os.system('git describe --tags'))

    return app
