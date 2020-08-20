from dotenv import load_dotenv
from lightbluetent.app import create_app
import os

app_env = os.getenv("APPLICATION_CONFIG", "production")
if app_env == "production":
    load_dotenv('.env')


# pass correct env value to application factory
app = create_app(os.getenv("FLASK_CONFIG"))