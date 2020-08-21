import os, subprocess
from flask import Flask
from . import admin, home, society

from .flask_seasurf import SeaSurf 
from flask_talisman import Talisman 

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

    app.config['CSRF_CHECK_REFERER'] = False
    csrf = SeaSurf(app)
    csp = {
        'default-src': [
            '\'self\'',
            'www.srcf.net'
        ],
        'img-src': [
            '\'self\'',
            'data:',
            'www.srcf.net'
        ]
    }
    Talisman(app, content_security_policy=csp) 

    from lightbluetent.models import db, migrate

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(admin.bp)
    app.register_blueprint(home.bp)
    app.register_blueprint(society.bp)

    @app.context_processor
    def inject_gh_rev():
        return dict(github_rev=subprocess.check_output(["git", "describe", "--tags"]).strip().decode())

    return app
