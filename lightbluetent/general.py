from flask import Blueprint, render_template, redirect, url_for, current_app
from lightbluetent.users import auth_decorator
from flask_babel import _
from lightbluetent.api import Meeting
from lightbluetent.models import Group
import random

bp = Blueprint("general", __name__)


@bp.route("/", methods=["GET"])
def index():
    # Check whether the directory page is enabled
    has_directory_page = current_app.config["HAS_DIRECTORY_PAGE"]

    if has_directory_page:
        groups = Group.query.all()

        running_meetings = {}
        for group in groups:
            meeting = Meeting(group)
            running_meetings[group.bbb_id] = meeting.is_running()

        # Shuffle the socs so they all have a chance of being near the top
        random.shuffle(groups)
        return render_template(
            "users/directory.html",
            page_title=_("Welcome to SRCF Events!"),
            groups=groups,
            running_meetings=running_meetings,
        )
    else:
        return render_template(
            "general/index.html",
            page_title=_("Welcome to SRCF Events!"),
        )


@bp.route("/logout")
def logout():
    auth_decorator.logout()
    return redirect(url_for("users.index"))


@bp.route("/log_in")
@auth_decorator
def log_in():
    return redirect(url_for("users.home"))
