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
from lightbluetent.models import db, Group, Room, User, Role, RoleType
from lightbluetent.users import auth_decorator
from lightbluetent.api import Meeting
from lightbluetent.utils import get_form_values, fetch_lookup_data
from flask_babel import _

bp = Blueprint("room_aliases", __name__)


@bp.route("/<room_alias>", methods=("GET", "POST"))
@bp.route("/r/<room_id>", methods=("GET", "POST"))
def home(room_id=None, room_alias=None):

    # is the user authenticated?
    crsid = auth_decorator.principal

    # get the current room
    if room_id:
        room = Room.query.filter_by(id=room_id).first()
        # If the room has an alias but wasn't accessed through it, redirect to the alias route.
        if not room:
            abort(404)
            
        if room.alias:
            return redirect(url_for("room_aliases.home", room_alias=room.alias))
    else:
        room = Room.query.filter_by(alias=room_alias).first()

    # fail if room is not found
    if not room:
        abort(404)

    # get room associated with the group, if any
    group = Group.query.filter_by(id=room.group_id).first()

    # create a BBB meeting instance
    meeting = Meeting(room)
    running = meeting.is_running()

    values = {}
    errors = {}

    if request.method == "POST":

        user = User.query.filter_by(crsid=crsid).first()

        #
        keys = ("name", "password")
        values = get_form_values(request, keys)

        # user made POST request but in the meantime meeting ended
        if not running:
            flash("This meeting is no longer running.")
            errors["running"] = "This meeting is no longer running."

        if len(values["name"]) <= 1:
            errors["name"] = "That name is too short."

        if room.authentication.value == "password":
            if values["password"] != room.password:
                errors["password"] = "Incorrect password."

        if errors:
            if room.group:
                return render_template(
                    "room_aliases/group.html",
                    page_title=f"{ room.name }",
                    room=room,
                    group=group,
                    user=user,
                    running=running,
                    errors=errors,
                    **values,
                    
                )
            else:
                return render_template(
                    "room_aliases/personal.html",
                    page_title=f"{ room.name }",
                    room=room,
                    user=user,
                    running=running,
                    errors=errors,
                    **values,
                )
        else:
            url = meeting.attendee_url(values["name"])
            return redirect(url)
    else:
        # GET request, loading the page
        
        # assume no user
        user = None

        raven_join_url = None

        # if authenticated
        if crsid:

            lookup_data = fetch_lookup_data(crsid)

            user = User.query.filter_by(crsid=crsid).first()
            if not user:
                # Create a visitor user if they're signed in with Raven but not actually in the DB
                user = User(
                    email=lookup_data["email"],
                    full_name=lookup_data["name"],
                    crsid=crsid,
                    role=Role.query.filter_by(role=RoleType("visitor")).first(),
                )
                db.session.add(user)
                current_app.logger.info(f"Registered visitor with CRSid { crsid }")
                db.session.commit()

            if room.authentication.value in ("raven", "whitelist") and user:
                raven_join_url = meeting.attendee_url(lookup_data["name"])

        if room.group:
            return render_template(
                "room_aliases/group.html",
                page_title=f"{ room.name }",
                raven_join_url=raven_join_url,
                room=room,
                group=group,
                user=user,
                running=running,
                errors=errors,
            )
        else:
            return render_template(
                "room_aliases/personal.html",
                page_title=f"{ room.name }",
                raven_join_url=raven_join_url,
                room=room,
                user=user,
                running=running,
                errors=errors,
            )

