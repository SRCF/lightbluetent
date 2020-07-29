import os

from lightbluetent.app import create_app

# pass correct env value to application factory
app = create_app(os.environ["FLASK_CONFIG"])
