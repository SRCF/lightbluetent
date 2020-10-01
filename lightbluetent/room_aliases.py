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
from lightbluetent.models import db, Group, Room, User
from lightbluetent.users import auth_decorator
from lightbluetent.api import Meeting
from lightbluetent.utils import (
    get_form_values,
    fetch_lookup_data
)
from flask_babel import _

bp = Blueprint("room_aliases", __name__)


@bp.route("/<room_alias>", methods=("GET", "POST"))
@bp.route("/r/<room_id>", methods=("GET", "POST"))
def home(room_id=None, room_alias=None):

    crsid = auth_decorator.principal

    if room_id:
        room = Room.query.filter_by(id=room_id).first()

        # If the room has an alias but wasn't accessed through it, redirect to the alias route.
        if room.alias:
            return redirect(url_for("room_aliases.home", room_alias=room.alias))

    else:
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

    values = {}
    errors = {}

    if request.method == "POST":

        keys = ("name", "password")
        values = get_form_values(request, keys)

        if not running:
            flash("This meeting is no longer running.")
            return render_template("room_aliases/home.html", page_title=f"{ room.name }",
                room=room, group=group, user=user, desc_paragraphs=desc_paragraphs,
                running=running, errors=errors, **values)

        if len(values["name"]) <= 1:
                errors["name"] = "That name is too short."

        if room.authentication.value == "password":

            if values["password"] != room.password:
                errors["password"] = "Incorrect password."

            if not errors:
                url = meeting.attendee_url(values["name"])
                return redirect(url)
            else:
                return render_template("room_aliases/home.html", page_title=f"{ room.name }",
                    room=room, group=group, user=user, desc_paragraphs=desc_paragraphs,
                    running=running, errors=errors, **values)

        # Public room
        else:

            if not errors:
                url = meeting.attendee_url(values["name"])
                return redirect(url)
            else:
                return render_template("room_aliases/home.html", page_title=f"{ room.name }",
                    room=room, group=group, user=user, desc_paragraphs=desc_paragraphs,
                    running=running, errors=errors, **values)


    # If not authenticated
    if not crsid:
        user = None
    else:
        user = User.query.filter_by(crsid=crsid).first()
        if not user:
            # Create a visitor user if they're signed in with Raven but not actually in the DB
            user = User(
                email=None,
                full_name=None,
                crsid=crsid,
                role=Role.query.filter_by(role=RoleType("visitor")).first(),
            )
            db.session.add(user)
            current_app.logger.info(
                f"Registered visitor with CRSid { crsid }"
            )
            db.session.commit()

    if room.authentication.value == "raven" or room.authentication.value == "whitelist":

        if user:
            lookup_data = fetch_lookup_data(crsid)
            raven_join_url = meeting.attendee_url(lookup_data["visibleName"])
        else:
            raven_join_url = None
    else:
        raven_join_url = None

    return render_template("room_aliases/home.html", page_title=f"{ room.name }", raven_join_url=raven_join_url,
        room=room, group=group, user=user, desc_paragraphs=desc_paragraphs,
        running=running, errors=errors)

