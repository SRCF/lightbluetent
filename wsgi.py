from lightbluetent.app import create_app
import os


# pass correct env value to application factory
app = create_app(os.getenv("FLASK_CONFIG"))