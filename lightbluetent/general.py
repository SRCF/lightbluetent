from flask import Blueprint, render_template, redirect, url_for, current_app
from lightbluetent.users import auth_decorator
from flask_babel import _
from lightbluetent.api import Meeting
from lightbluetent.models import Society
import random

bp = Blueprint("general", __name__)


@bp.route("/", methods=["GET"])
def index():
    # Check whether the directory page is enabled
    has_directory_page = current_app.config["HAS_DIRECTORY_PAGE"]

    if has_directory_page:
        societies = Society.query.all()

        running_meetings = {}
        for society in societies:
            meeting = Meeting(society)
            running_meetings[society.bbb_id] = meeting.is_running()

        # Shuffle the socs so they all have a chance of being near the top
        random.shuffle(societies)
        return render_template(
            "users/directory.html",
            page_title=_("Welcome to the 2020 Virtual Freshers' Fair!"),
            societies=societies,
            running_meetings=running_meetings,
        )
    else:
        return render_template(
            "general/index.html",
            page_title=_("Welcome to the 2020 Virtual Freshers' Fair!"),
        )


@bp.route("/logout")
def logout():
    auth_decorator.logout()
    return redirect(url_for("users.index"))


@bp.route("/log_in")
@auth_decorator
def log_in():
    return redirect(url_for("users.home"))
