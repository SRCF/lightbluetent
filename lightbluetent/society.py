import re
import os

from flask import Blueprint, render_template, request, flash, abort, redirect, url_for, current_app
from lightbluetent.models import db, Society, User
from lightbluetent.home import auth_decorator
from lightbluetent.api import Meeting
from flask_babel import _

bp = Blueprint("society", __name__, url_prefix="/s")

email_re = re.compile(r"^\S+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+$")

@bp.route("/<uid>", methods=("GET", "POST"))
def welcome(uid):

    society = Society.query.filter_by(uid=uid).first()

    if not society:
        return abort(404)

    desc_paragraphs = {}
    # Split the description into paragraphs so it renders nicely.
    if society.description is not None:
        desc_paragraphs=society.description.split("\n")

    sessions_data = {"days": current_app.config["NUMBER_OF_DAYS"]}

    has_logo = True
    if society.logo == current_app.config["DEFAULT_LOGO"]:
        has_logo = False

    meeting = Meeting(society)
    running = meeting.is_running()

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()

        errors = {}
        if len(full_name) <= 1:
            errors["full_name"] = "That name is too short."

        if errors:
            return render_template("society/welcome.html", page_title=f"{ society.name }",
                           society=society, desc_paragraphs=desc_paragraphs,
                           sessions_data=sessions_data, has_logo=has_logo, running=running,
                           errors=errors)

        if not running:
            flash("The meeting is no longer running.")
        elif full_name != "":
            url = meeting.attendee_url(full_name)

            # TODO: should we be logging this?
            current_app.logger.info(f"Attendee '{ full_name }' joined stall for '{ society.name }', bbb_id: '{ society.bbb_id }'")

            return redirect(url)

    return render_template("society/welcome.html", page_title=f"{ society.name }",
                           society=society, desc_paragraphs=desc_paragraphs,
                           sessions_data=sessions_data, has_logo=has_logo, running=running,
                           errors={})


# Check if a meeting is running. If it's not, create it. Redirect to the URL to
# join that meeting as a moderator with the provided name.
@bp.route("/<uid>/begin", methods=("GET", "POST"))
@auth_decorator
def begin_session(uid):

    society = Society.query.filter_by(uid=uid).first()

    if not society:
        return abort(404)

    crsid = auth_decorator.principal
    user = User.query.filter_by(crsid=crsid).first()
    if society not in user.societies:
        abort(403)

    meeting = Meeting(society)
    running = meeting.is_running()

    if running:
        page_title = "Join session"
    else:
        page_title = "Begin session"

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()

        errors = {}
        if len(full_name) <= 1:
            errors["full_name"] = "That name is too short."

        if errors:
            return render_template("society/begin_session.html", page_title=page_title,
                           user=user, running=running, page_parent=url_for("home.home"), errors=errors)

        if not running:
            join_url = url_for("society.welcome", uid=society.uid, _external=True)
            moderator_only_message = _("To invite others into this session, share your stall link: %(join_url)s", join_url=join_url)
            success, message = meeting.create(moderator_only_message)
            current_app.logger.info(f"Moderator '{ full_name }' with CRSid '{ crsid }' created stall for '{ society.name }', bbb_id: '{ society.bbb_id }'")

            if success:
                url = meeting.moderator_url(full_name)
                return redirect(url)
            else:
                # For some reason the meeting wasn't created.
                current_app.logger.error(f"Creation of stall failed: { message }")
                flash(f"The session could not be created. Please contact an administrator at support@srcf.net and include the following: { message }")

        else:
            url = meeting.moderator_url(full_name)
            current_app.logger.info(f"Moderator '{ full_name }' with CRSid '{ crsid }' joined stall for '{ society.name }', bbb_id: '{ society.bbb_id }'")
            return redirect(url)

    return render_template("society/begin_session.html", page_title=page_title,
                           user=user, running=running, page_parent=url_for("home.home"), errors={})
