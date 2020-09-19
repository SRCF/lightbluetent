import re
import os

from flask import Blueprint, render_template, request, flash, abort, redirect, url_for, current_app
from lightbluetent.models import db, Society, User
from lightbluetent.home import auth_decorator
from lightbluetent.api import ModeratorMeeting, AttendeeMeeting
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

    meeting = AttendeeMeeting(society.bbb_id, society.attendee_pw, society.bbb_logo)
    running = meeting.is_running()

    if request.method == "POST":

        # We should only be able to submit a POST request if the meeting is running.
        # TODO: there may be circumstances where the meeting was running when this page was
        # loaded, but it is no longer running when we submit this POST request. How should
        # we handle this, if at all? Currently we abort(500).

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
            abort(500)

        if full_name != "":
            url = meeting.get_join_url(full_name)

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

    join_url = url_for("society.welcome", uid=society.uid, _external=True)
    moderator_only_message = _("To invite others into this session, share your stall link: %(join_url)s", join_url=join_url)

    meeting = ModeratorMeeting(society.name,
                               society.bbb_id,
                               society.attendee_pw,
                               society.moderator_pw,
                               society.welcome_text,
                               moderator_only_message,
                               society.bbb_logo,
                               society.banner_text,
                               society.banner_color,
                               society.mute_on_start,
                               society.disable_private_chat)

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
                           crsid=crsid, running=running, page_parent=url_for("home.home"), errors=errors)

        if not running:
            success, message = meeting.create()
            current_app.logger.info(f"Moderator '{ full_name }' with CRSid '{ crsid }' created stall for '{ society.name }', bbb_id: '{ society.bbb_id }'")

            if success:
                url = meeting.get_join_url(full_name)
                return redirect(url)
            else:
                # For some reason the meeting wasn't created.
                current_app.logger.info(f"Creation of stall failed: { message }")
                abort(500)


        else:
            url = meeting.get_join_url(full_name)
            current_app.logger.info(f"Moderator '{ full_name }' with CRSid '{ crsid }' joined stall for '{ society.name }', bbb_id: '{ society.bbb_id }'")
            return redirect(url)

    return render_template("society/begin_session.html", page_title=page_title,
                           crsid=crsid, running=running, page_parent=url_for("home.home"), errors={})
