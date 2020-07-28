from flask import Flask
from . import utils, home
import logging
import os
import jinja2
from werkzeug.contrib.fixers import ProxyFix

DOMAIN_WEB = "https://freshers.srcf.net"

# def make_app(app):
#     app.errorhandler(400)(utils.generic_error_handler)
#     for error in range(402, 432):
#         app.errorhandler(error)(utils.generic_error_handler)
#     for error in range(500, 504):
#         app.errorhandler(error)(utils.generic_error_handler)

#     app.jinja_env.globals["sif"] = utils.sif
#     app.jinja_env.undefined = jinja2.StrictUndefined

#     if not app.secret_key and 'FLASK_SECRET_KEY' in os.environ:
#         app.secret_key = os.environ['FLASK_SECRET_KEY']

#     if not app.request_class.trusted_hosts and 'FLASK_TRUSTED_HOSTS' in os.environ:
#         app.request_class.trusted_hosts = os.environ['FLASK_TRUSTED_HOSTS'].split(",")

#     # Make request.remote_addr work etc. (only safe if we are behind a proxy, which we always should be)
#     app.wsgi_app = ProxyFix(app.wsgi_app)


app = Flask(__name__,
            template_folder="../templates",
            static_folder="../static")

app.jinja_env.globals["DOMAIN_WEB"] = DOMAIN_WEB
logging.basicConfig(level=logging.DEBUG if app.debug else logging.INFO)
app.register_blueprint(home.bp)
