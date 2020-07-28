from flask import Flask
from . import utils, home
import logging

app = Flask(__name__,
            template_folder="../templates",
            static_folder="../static")

logging.basicConfig(level=logging.DEBUG if app.debug else logging.INFO)

DOMAIN_WEB = "https://freshers.srcf.net"

app.register_blueprint(home.bp)
