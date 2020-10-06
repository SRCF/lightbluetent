import os, subprocess, logging
import logging.handlers
from flask import Flask
from werkzeug.exceptions import HTTPException
from . import rooms, users, society, admins, general
from .flask_seasurf import SeaSurf
from flask_talisman import Talisman
from flask_babel import Babel
from .utils import gen_unique_string, ordinal, sif, page_not_found, server_error, table_exists
from lightbluetent.models import db, migrate, Setting, Role, Permission, User
from functools import wraps
import click


def configure_logging(app):
    # TODO: we probably want to manage the logging in more detail using logging.config.dictConfig;
    #       for now, we just extend the default [gunicorn logger][1]
    # [1]: https://trstringer.com/logging-flask-gunicorn-the-manageable-way/

    if not app.config['PRODUCTION']:
        print("Development environment, using stderr for logging.")
        return

    gunicorn_logger = logging.getLogger("gunicorn.error")

    if (email_config := app.config.get('EMAIL_CONFIGURATION')) is not None:
        email_config['toaddrs'] = app.config['MAINTAINERS']
        mail_handler = logging.handlers.SMTPHandler(**email_config)
        mail_handler.setLevel(logging.ERROR)
        gunicorn_logger.addHandler(mail_handler)

    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

    @app.errorhandler(Exception)
    def exception_interceptor(e):
        if isinstance(e, HTTPException):
            code = e.code
            if (code // 100) == 3:
                # redirection, this probably never gets called though...
                return e.get_response(request.environ), code
        app.logger.exception(e)
        return server_error(e)

    @app.route('/oops')
    def oops():
        1/0


def logging_wrapper(log_fun):
    def decorator(f):
        @wraps(f)
        def wrapped(e, *a, **k):
            log_fun(e)
            return f(e, *a, **k)
        return wrapped
    return decorator


def create_app(config_name=None):

    if config_name == None:
        config_name = "production"

    app = Flask(__name__, template_folder="templates")

    config_module = f"lightbluetent.config.{config_name.capitalize()}Config"
    app.config.from_object(config_module)
    configure_logging(app)

    if not app.secret_key and "FLASK_SECRET_KEY" in os.environ:
        app.secret_key = os.environ["FLASK_SECRET_KEY"]

    if not app.request_class.trusted_hosts and "FLASK_TRUSTED_HOSTS" in os.environ:
        app.request_class.trusted_hosts = os.environ["FLASK_TRUSTED_HOSTS"].split(",")

    app.config["CSRF_CHECK_REFERER"] = False
    csrf = SeaSurf(app)
    csp = {
        "default-src": ["'self'", "www.srcf.net"],
        "img-src": ["'self'", "data:", "www.srcf.net"],
        "style-src": ["'self'", "'unsafe-inline'", "www.srcf.net"],
    }
    Talisman(app, content_security_policy=csp)

    babel = Babel(app)

    app.jinja_env.globals["sif"] = sif
    app.jinja_env.globals["gen_unique_string"] = gen_unique_string
    app.jinja_env.globals["ordinal"] = ordinal

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(general.bp)
    app.register_blueprint(rooms.bp)
    app.register_blueprint(users.bp)
    app.register_blueprint(society.bp)
    app.register_blueprint(admins.bp)
    app.register_error_handler(404, logging_wrapper(app.logger.info)(page_not_found))
    app.register_error_handler(500, logging_wrapper(app.logger.exception)(server_error))

    @app.context_processor
    def inject_gh_rev():
        return dict(github_rev=app.config['GITHUB_REV'])

    @app.template_test()
    def equalto(value, other):
        return value == other

    @app.cli.command("change-role")
    @click.argument("crsids", nargs=-1)
    @click.argument("role", nargs=1)
    def create_user(crsids, role):
        """ Allows an admin to change a user's role """
        with app.app_context():
            for crsid in crsids:
                user = User.query.filter_by(crsid=crsid).first()
                role = Role.query.filter_by(name=role.lower()).first()
                prev_role = user.role
                if role:
                    user.role = role
                    db.session.commit()
                    click.echo(f"Changed {user.full_name}'s role from {prev_role.name} to {role.name}")
                else:
                    click.echo("Role does not exist")

    with app.app_context():
        # create seed values for settings if not already present
        if table_exists("settings"):
            for setting in app.config["SITE_SETTINGS"]:
                has_setting = Setting.query.filter_by(name=setting["name"]).first()
                if not has_setting:
                    new_setting = Setting(name=setting["name"], enabled=setting["enabled"])
                    db.session.add(new_setting)

        if table_exists("permissions"):
            for perm in app.config["DEFAULT_PERMS"]:
                has_perm = Role.query.filter_by(name=perm["name"]).first()
                if not has_perm:
                    new_perm = Permission(name=perm["name"])
                    db.session.add(new_perm)

        if table_exists("roles"):
            for role in app.config["DEFAULT_ROLES"]:
                has_role = Role.query.filter_by(name=role["name"]).first()
                if not has_role:
                    new_role = Role(name=role["name"], description=role["description"])
                    new_role.permission = Permission.query.filter_by(
                        name=role["permission"]
                    ).first()
                    db.session.add(new_role)

        db.session.commit()

    return app
