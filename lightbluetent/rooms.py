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
from lightbluetent.models import db, User, Group, Room, Authentication, Role, Recurrence, Session
from lightbluetent.config import RoleType
from lightbluetent.users import auth_decorator
from lightbluetent.api import Meeting
from lightbluetent.utils import (
    gen_unique_string,
    delete_logo,
    get_form_values,
    fetch_lookup_data,
    validate_room_alias,
    validate_date
)
from PIL import Image
from flask_babel import _
from datetime import time, datetime
from sqlalchemy.orm.attributes import flag_modified

bp = Blueprint("rooms", __name__, url_prefix="/r")

@bp.route("/<room_id>/begin", methods=("GET", "POST"))
def begin(room_id):

    room = Room.query.filter_by(id=room_id).first()

    if not room:
        abort(404)

    group = None

    crsid = auth_decorator.principal

    if crsid is None:
        abort(403)

    user = User.query.filter_by(crsid=crsid).first()

    # If this room is associated with a group
    if room.group_id:
        group = Group.query.filter_by(id=group_id).first()

        # ensure that the user belongs to the group they're editing
        if group not in user.groups:
            abort(403)
    elif room.user_id:
        if user.id != room.user_id:
            abort(403)
    else:
        current_app.logger.error(f"Room { room.name } has neither a group_id nor a user_id.")
        abort(500)


    lookup_data = fetch_lookup_data(crsid)
    full_name = lookup_data["visibleName"]

    meeting = Meeting(room)
    running = meeting.is_running()

    if not running:

        if room.alias:
            join_url = url_for("room_aliases.home", room_alias=room.alias, _external=True)
        else:
            join_url = url_for("room_aliases.home", id=room.id, _external=True)
        moderator_msg = _("To invite others to this event, share your room link: %(join_url)s", join_url=join_url)

        success, message = meeting.create(moderator_msg)
        current_app.logger.info(f"User '{ full_name }' with CRSid '{ crsid }' created room '{ room.name }', meetingID: '{ room.id }'")

        if success:
            url = meeting.moderator_url(full_name)
            return redirect(url)
        else:
            # For some reason the meeting wasn't created.
            current_app.logger.error(f"Creation of stall failed: { message }")
            flash(f"The meeting could not be created. Please contact an administrator at support@srcf.net and include the following: { message }")

    else:
        url = meeting.moderator_url(full_name)
        return redirect(url)

@bp.route("/<room_id>/update/<update_type>", methods=["POST"])
@auth_decorator
def update(room_id, update_type):
    # first pass: is the room URL valid?
    room = Room.query.filter_by(id=room_id).first()
    if not room:
        abort(404)

    # second pass: does the room belong to the user?
    # or does it belong to a user's group?
    crsid = auth_decorator.principal
    user = User.query.filter_by(crsid=crsid).first()
    if room.group_id:
        parent_page = url_for("groups.manage", group_id=room.group.id)
        group_id = room.group_id
        group = Group.query.filter_by(id=group_id).first()
        if group not in user.groups:
            abort(403)
    else:
        parent_page = url_for("users.home")
        group = None
        if room not in user.rooms:
            abort(403)

    errors = {}

    keys = ("name", "authentication", "password", "whitelist", "alias", "description",
            "start_date", "start_hour", "start_min", "end_date", "end_hour", "end_min", "frequency", "limit", "limit_count", "limit_until",
            "welcome_text", "banner_text", "banner_color"
    )
    values = get_form_values(request, keys)

    for key in ("recurring", "alias_checked"):
        values[key] = bool(request.form.get(key, False))

    if update_type == "room_details":

        if len(values["whitelist"]) > 7:
            errors["whitelist"] = "Invalid CRSid."

        if start_date_entered or end_date_entered:
            if not full_start_date:
                errors["start"] = "Enter a full date and time."
            if not full_end_date:
                errors["end"] = "Enter a full date and time."

        if values["alias_checked"]:
            if values["alias"] == "":
                errors["alias"] = "You must specify the name of your alias."
            elif not validate_room_alias(values["alias"]):
                errors["alias"] = "Invalid alias."

            room_with_alias = Room.query.filter_by(alias=values["alias"]).first()

            if room_with_alias and room_with_alias.id != room.id:
                errors["alias"] = "That URL is already in use. Choose a different one."

        if values["whitelist"] != "":
            current_app.logger.info(
                f"{ crsid } is whitelisting '{ values['whitelist'] }' for room '{ room.id }'..."
            )

            # Whitelist a new CRSid.
            # We check if the user's already registered. If not, we create a
            # visitor user containing only the whitelisted CRSid.

            existing_user = User.query.filter_by(crsid=values["whitelist"]).first()
            if existing_user:
                room.whitelisted_users.append(existing_user)
            else:
                user = User(
                    email=None,
                    full_name=None,
                    crsid=values["whitelist"],
                    role=Role.query.filter_by(role=RoleType("visitor")).first(),
                )
                db.session.add(user)
                current_app.logger.info(
                    f"Registered visitor with CRSid { values['whitelist'] }"
                )
                room.whitelisted_users.append(user)

        if not errors:
            room.name = values["name"]
            room.authentication = Authentication(values["authentication"])
            room.description = values["description"]
            room.alias = values["alias"] if values["alias"] != "" else None


    elif update_type == "room_times":

        # Is there a better way to do this?
        valid_start_date = validate_date(values["start_date"]) and values["start_hour"].isdigit() and values["start_min"].isdigit()
        valid_end_date = validate_date(values["end_date"]) and values["end_hour"].isdigit() and values["end_min"].isdigit()

        if not valid_start_date:
            errors["start"] = "You must specify a starting time and date."
        elif not valid_end_date:
            errors["end"] = "You must specify a ending time and date."
        else:
            if int(values["start_hour"]) > 24 or int(values["start_min"]) > 60:
                errors["start"] = "Invalid start time."
            if int(values["end_hour"]) > 24 or int(values["end_min"]) > 60:
                errors["end"] = "Invalid end time."

            start_date = values["start_date"].split("-")
            start_year = int(start_date[0])
            start_month = int(start_date[1])
            start_day = int(start_date[2])

            end_date = values["end_date"].split("-")
            end_year = int(end_date[0])
            end_month = int(end_date[1])
            end_day = int(end_date[2])

            start = datetime(start_year, start_month, start_day, int(values["start_hour"]), int(values["start_min"]))
            end = datetime(end_year, end_month, end_day, int(values["end_hour"]), int(values["end_min"]))

            limit_until = None
            limit_count = None

            if values["recurring"]:

                if values["frequency"] == "":
                    errors["frequency"] = "Select a frequency of recurrence."
                if values["limit"] == "":
                    errors["limit"] = "Select when the event will end."
                valid_frequency = (values["frequency"] == "daily"
                        or values["frequency"] == "weekdays"
                        or values["frequency"] == "weekly"
                        or values["frequency"] == "monthly"
                        or values["frequency"] == "yearly")

                valid_limit = (values["limit"] == "forever"
                        or values["limit"] == "until"
                        or values["limit"] == "count")

                if not valid_frequency:
                    errors["frequency"] = "Invalid frequency of recurrence."
                if not valid_limit:
                    errors["limit"] = "Invalid recurrence limit."

                if values["limit"] == "until":
                    if not validate_date(values["limit_until"]):
                        errors["limit"] = "Invalid finishing date."
                    else:
                        until_date = values["limit_until"].split("-")
                        until_year = int(until_date[0])
                        until_month = int(until_date[1])
                        until_day = int(until_date[2])

                        limit_until = datetime(until_year, until_month, until_day)

                elif values["limit"] == "count":
                    if values["limit_count"] == "":
                        errors["limit_count"] == "You must specify when the recurrence finishes."
                    else:
                        limit_count = values["limit_count"]

        if not errors:
            if not values["recurring"]:
                session = Session(
                    room_id=room.id,
                    start=start,
                    end=end,
                    recur=Recurrence.NONE,
                )
            else:
                if limit_until:
                    session = Session(
                        room_id=room.id,
                        start=start,
                        end=end,
                        recur=Recurrence(values["frequency"]),
                        until=limit_until
                    )
                elif limit_count:
                    session = Session(
                        room_id=room.id,
                        start=start,
                        end=end,
                        recur=Recurrence(values["frequency"]),
                        count=limit_count
                    )
                else:
                    session = Session(
                        room_id=room.id,
                        start=start,
                        end=end,
                        recur=Recurrence(values["frequency"]),
                    )

            db.session.add(session)


    elif update_type == "room_features":

        for key in ("mute_on_start", "disable_private_chat"):
            values[key] = bool(request.form.get(key, False))

        if len(values["welcome_text"]) > 500:
            errors["welcome_text"] = "Welcome text is too long."
        if len(values["banner_text"]) > 200:
            errors["banner_text"] = "Banner text is too long."

        if not errors:
            room.welcome_text = values["welcome_text"] if values["welcome_text"] != "" else None
            room.banner_text = values["banner_text"] if values["banner_text"] != "" else None
            room.banner_color = values["banner_color"]

            room.mute_on_start = values["mute_on_start"]
            room.disable_private_chat = values["disable_private_chat"]

    else:
        current_app.logger.error(
            f"Attempted to update room page at incorrect endpoint: {update_type}"
        )

    if errors:
        flash(_("There were problems with the information you provided."), "error")
        return render_template(
            "rooms/manage.html",
            page_title=f"Settings for { room.name }",
            room=room,
            user=user,
            group=group,
            errors=errors,
            page_parent=parent_page,
            **values
        )
    else:
        room.updated_at = datetime.now()
        db.session.commit()
        flash("Settings saved.", "success")
        return redirect(url_for("rooms.manage", room_id=room.id))



@bp.route("/<room_id>/manage", methods=["GET"])
@auth_decorator
def manage(room_id):
    # first pass: is the room URL valid?
    room = Room.query.filter_by(id=room_id).first()
    if not room:
        abort(404)

    # second pass: does the room belong to the user?
    # or does it belong to a user's group?
    crsid = auth_decorator.principal
    user = User.query.filter_by(crsid=crsid).first()

    # third pass: does the user even exist?
    if not user:
        return redirect(url_for("users.register"))

    if room.group_id:
        parent_page = url_for("groups.manage", group_id=room.group.id)
        group_id = room.group_id
        group = Group.query.filter_by(id=group_id).first()
        if group not in user.groups:
            abort(403)
    else:
        parent_page = url_for("users.home")
        group = None
        if room not in user.rooms:
            abort(403)

    # Defaults
    values = {
        "name": room.name,
        "welcome_text": room.welcome_text,
        "banner_text": room.banner_text,
        "banner_color": room.banner_color,
        "authentication": room.authentication,
        "alias": room.alias,
        "mute_on_start": room.mute_on_start,
        "disable_private_chat": room.disable_private_chat,
        "start_date": None,
        "start_hour": None,
        "start_min": None,
        "end_date": None,
        "end_hour": None,
        "end_min": None,
        "recurring": False
    }

    return render_template(
        "rooms/manage.html",
        page_title=f"Settings for { room.name }",
        room=room,
        user=user,
        group=group,
        errors={},
        page_parent=parent_page,
        **values,
    )


@bp.route("/<room_id>/new_password")
@auth_decorator
def new_password(room_id):

    room = Room.query.filter_by(id=room_id).first()

    if not room:
        abort(404)

    group = None

    crsid = auth_decorator.principal

    if crsid is None:
        abort(403)

    user = User.query.filter_by(crsid=crsid).first()

    # If this room is associated with a group
    if room.group_id:
        group = Group.query.filter_by(id=room.group_id).first()

        # ensure that the user belongs to the group they're editing
        if group not in user.groups:
            abort(403)
    elif room.user_id:
        if user.id != room.user_id:
            abort(403)
    else:
        current_app.logger.error(f"Room { room.name } has neither a group_id nor a user_id.")
        abort(500)


    new_pw = gen_unique_string()[0:6]

    room.password = new_pw
    db.session.commit()

    return redirect(url_for("rooms.manage", id=room.id))

@bp.route("/<room_id>/unwhitelist/<crsid_to_remove>")
@auth_decorator
def unwhitelist(room_id, crsid_to_remove):

    room = Room.query.filter_by(id=room_id).first()

    if not room:
        abort(404)

    group = None

    crsid = auth_decorator.principal

    if crsid is None:
        abort(403)

    user = User.query.filter_by(crsid=crsid).first()

    # If this room is associated with a group
    if room.group_id:
        group = Group.query.filter_by(id=group_id).first()

        # ensure that the user belongs to the group they're editing
        if group not in user.groups:
            abort(403)
    elif room.user_id:
        if user.id != room.user_id:
            abort(403)
    else:
        current_app.logger.error(f"Room { room.name } has neither a group_id nor a user_id.")
        abort(500)


    user_to_remove = User.query.filter_by(crsid=crsid_to_remove).first()

    if not user_to_remove:
        abort(404)

    room.whitelisted_users.remove(user_to_remove)
    db.session.commit()

    return redirect(url_for("rooms.manage", id=room.id))


@bp.route("/<room_id>/delete", methods=("GET", "POST"))
@auth_decorator
def delete(room_id):

    room = Room.query.filter_by(id=room_id).first()

    if not room:
        abort(404)

    group = None

    crsid = auth_decorator.principal

    if crsid is None:
        abort(403)

    user = User.query.filter_by(crsid=crsid).first()

    # If this room is associated with a group
    if room.group_id:
        group = Group.query.filter_by(id=room.group_id).first()

        # ensure that the user belongs to the group they're editing
        if group not in user.groups:
            abort(403)
    elif room.user_id:
        if user.id != room.user_id:
            abort(403)
    else:
        current_app.logger.error(f"Room { room.name } has neither a group_id nor a user_id.")
        abort(500)


    db.session.delete(room)
    db.session.commit()

    current_app.logger.info(
        f"User { crsid } deleted room with id = '{ room.id }'"
    )

    return redirect(url_for("groups.manage", group_id=group.id))


