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
from lightbluetent.models import db, User, Group, Room, Authentication, Role
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
def home(room_alias):

    room = Room.query.filter_by(alias=room_alias).first()

    if not room:
        abort(404)

    group = Group.query.filter_by(id=room.group_id).first()

    desc_paragraphs = {}
    # Split the description into paragraphs so it renders nicely.
    if room.description is not None:
        desc_paragraphs=room.description.split("\n")

    meeting = Meeting(room)
    running = meeting.is_running()

    errors = {}

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()

        errors = {}
        if len(full_name) <= 1:
            errors["full_name"] = "That name is too short."

        if errors:
            return render_template("rooms/home.html", page_title=f"{ room.name }",
                           room=room, group=group, desc_paragraphs=desc_paragraphs,
                           running=running, errors=errors)

        if not running:
            flash("The meeting is no longer running.")
        else:
            url = meeting.attendee_url(full_name)
            return redirect(url)

    else:
        return render_template("rooms/home.html", page_title=f"{ room.name }",
                           room=room, group=group, desc_paragraphs=desc_paragraphs,
                           running=running, errors=errors)


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
            "authentication",
            "password",
            "whitelist"
        )
        values = get_form_values(request, keys)

        for key in ("mute_on_start", "disable_private_chat"):
            values[key] = bool(request.form.get(key, False))

        if len(values["welcome_text"]) > 500:
            errors["welcome_text"] = "Welcome text is too long."
        if len(values["banner_text"]) > 200:
            errors["banner_text"] = "Banner text is too long."

        if len(values["whitelist"]) > 7:
            errors["whitelist"] = "Invalid CRSid."

        if not errors:
            room.name = values["name"]
            room.welcome_text = values["welcome_text"] if values["welcome_text"] != "" else None
            room.banner_text = values["banner_text"] if values["banner_text"] != "" else None
            room.banner_color = values["banner_color"]
            room.authentication = Authentication(values["authentication"])
            room.mute_on_start = values["mute_on_start"]
            room.disable_private_chat = values["disable_private_chat"]
            room.updated_at = datetime.now()

            if values["whitelist"] != "":

                current_app.logger.info(
                    f"{ crsid } is whitelisting '{ values['whitelist'] }' for room '{ group.id }/{ room.name }'..."
                )

                # Whitelist a new CRSid.
                # We check if the user's already registered. If not, we create a
                # dummy user containing only the whitelisted CRSid.
                # TODO: sign-up code must be changed to account for users with NULL email and full_name.

                existing_user = User.query.filter_by(crsid=values["whitelist"]).first()
                if existing_user:
                    room.whitelisted_users.append(existing_user)
                else:
                    user = User(
                        email=None,
                        full_name=None,
                        crsid=values["whitelist"],
                        role=Role.query.filter_by(name="user").first(),
                    )
                    db.session.add(user)
                    current_app.logger.info(
                        f"Registered dummy user with CRSid { values['whitelist'] }"
                    )
                    db.session.commit()

                    room.whitelisted_users.append(user)

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
                group=group,
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
        "authentication": room.authentication,
        "mute_on_start": room.mute_on_start,
        "disable_private_chat": room.disable_private_chat
    }

    return render_template(
        "rooms/manage.html",
        page_title=f"Settings for { room.name }",
        room=room,
        group=group,
        user=user,
        errors={},
        page_parent=url_for("groups.manage", group_id=group.id),
        **values,
    )


@bp.route("/<room_alias>/new_password")
@auth_decorator
def new_password(room_alias):
    room = Room.query.filter_by(alias=room_alias).first()
    if not room:
        abort(404)

    crsid = auth_decorator.principal
    user = User.query.filter_by(crsid=crsid).first()
    group = Group.query.filter_by(id=room.group_id).first()

    if group not in user.groups:
        abort(403)

    new_pw = gen_unique_string()[0:6]

    room.password = new_pw
    db.session.commit()

    return redirect(url_for("rooms.manage", room_alias=room.alias))

@bp.route("/<room_alias>/unwhitelist/<crsid_to_remove>")
@auth_decorator
def unwhitelist(room_alias, crsid_to_remove):

    room = Room.query.filter_by(alias=room_alias).first()
    if not room:
        abort(404)

    crsid = auth_decorator.principal
    user = User.query.filter_by(crsid=crsid).first()
    group = Group.query.filter_by(id=room.group_id).first()

    if group not in user.groups:
        abort(403)

    user_to_remove = User.query.filter_by(crsid=crsid_to_remove).first()

    if not user_to_remove:
        abort(404)

    room.whitelisted_users.remove(user_to_remove)
    db.session.commit()

    return redirect(url_for("rooms.manage", room_alias=room.alias))


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
