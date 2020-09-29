import os
import copy

from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    abort,
    redirect,
    url_for,
    current_app,
)
from lightbluetent.models import db, User, Group, Room
from lightbluetent.users import auth_decorator
from lightbluetent.api import Meeting
from lightbluetent.utils import (
    gen_unique_string,
    delete_logo,
    get_form_values,
)
from PIL import Image
from flask_babel import _
from datetime import time, datetime
from sqlalchemy.orm.attributes import flag_modified

bp = Blueprint("rooms", __name__, url_prefix="/r")


@bp.route("/<room_alias>", methods=("GET", "POST"))
def room_home(room_alias):

    room = Room.query.filter_by(alias=room_alias).first()

    desc_paragraphs = {}
    # Split the description into paragraphs so it renders nicely.
    if room.description is not None:
        desc_paragraphs=room.description.split("\n")

    room = Room(group)
    running = room.is_running()

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()

        errors = {}
        if len(full_name) <= 1:
            errors["full_name"] = "That name is too short."

        if errors:
            return render_template("rooms/room_home.html", page_title=f"{ room.name }",
                           room=room, desc_paragraphs=desc_paragraphs,
                           sessions_data=sessions_data, has_logo=has_logo, running=running,
                           errors=errors)

        if not running:
            flash("The meeting is no longer running.")
        else:
            url = meeting.attendee_url(full_name)
            return redirect(url)

    else:
        return render_template("rooms/room_home.html", page_title=f"{ room.name }",
                           room=room, desc_paragraphs=desc_paragraphs,
                           sessions_data=sessions_data, has_logo=has_logo, running=running,
                           errors=errors)


@bp.route("/<room_alias>/manage", methods=("GET", "POST"))
@auth_decorator
def manage(room_alias):

    has_directory_page = current_app.config["HAS_DIRECTORY_PAGE"]

    room = Room.query.filter_by(alias=room_alias).first()
    group_id = room.group_id
    group = Group.query.filter_by(id=group_id).first()

    if not room:
        abort(404)

    # ensure that the user belongs to the group they're editing
    crsid = auth_decorator.principal
    user = User.query.filter_by(crsid=crsid).first()
    if group not in user.groups:
        abort(403)

    values = {}
    errors = {}

    if request.method == "POST":
        keys = (
            "name",
            "welcome_text",
            "banner_text",
            "banner_color",
        )
        values = get_form_values(request, keys)

        for key in ("mute_on_start", "disable_private_chat"):
            values[key] = bool(request.form.get(key, False))

        if len(values["welcome_text"]) > 500:
            errors["welcome_text"] = "Welcome text is too long."
        if len(values["banner_text"]) > 200:
            errors["banner_text"] = "Banner text is too long."

        if not errors:
            room.name = values["name"]
            room.welcome_text = values["welcome_text"] if values["welcome_text"] != "" else None
            room.banner_text = values["banner_text"] if values["banner_text"] != "" else None
            room.banner_color = values["banner_color"]
            room.mute_on_start = values["mute_on_start"]
            room.disable_private_chat = values["disable_private_chat"]
            room.updated_at = datetime.now()

            db.session.commit()

            flash("Settings saved.")
            return redirect(url_for("rooms.manage", room_alias=room.alias))

        else:
            flash(_("There were problems with the information you provided."))
            return render_template(
                "rooms/manage.html",
                page_title=f"Settings for { room.name }",
                room=room,
                user=user,
                errors=errors,
                page_parent=url_for("groups.manage", group_id=group.id),
                **values
            )


    # Defaults
    values = {
        "name": room.name,
        "welcome_text": room.welcome_text,
        "banner_text": room.banner_text,
        "banner_color": room.banner_color,
        "mute_on_start": room.mute_on_start,
        "disable_private_chat": room.disable_private_chat
    }

    return render_template(
        "rooms/manage.html",
        page_title=f"Settings for { room.name }",
        room=room,
        user=user,
        errors={},
        page_parent=url_for("groups.manage", group_id=group.id),
        **values,
    )


@bp.route("/<room_alias>/delete", methods=("GET", "POST"))
@auth_decorator
def delete(room_alias):

    room = Room.query.filter_by(alias=room_alias).first()
    if not room:
        abort(404)

    crsid = auth_decorator.principal
    user = User.query.filter_by(crsid=crsid).first()
    group = Group.query.filter_by(id=room.group_id).first()

    if group not in user.groups:
        abort(403)

    db.session.delete(room)
    db.session.commit()

    current_app.logger.info(
        f"User { crsid } deleted room with alias='{ room.alias }'"
    )

    return redirect(url_for("groups.manage", group_id=group.id))
