from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    url_for,
    redirect,
    abort,
    current_app,
)
from lightbluetent.models import db, User, Group, Setting, Role, Room, Authentication
from lightbluetent.config import RoleType
from lightbluetent.utils import (
    gen_unique_string,
    gen_room_id,
    validate_email,
    fetch_lookup_data,
    validate_short_name,
    get_form_values,
)
from flask_babel import _

import ucam_webauth
import ucam_webauth.raven
import ucam_webauth.raven.flask_glue

import json

bp = Blueprint("users", __name__, url_prefix="/u")

auth_decorator = ucam_webauth.raven.flask_glue.AuthDecorator(
    desc=_("SRCF Events"), require_ptags=None
)


@bp.route("/home")
@auth_decorator
def home():
    crsid = auth_decorator.principal

    user = User.query.filter_by(crsid=crsid).first()

    if not user:
        return redirect(url_for("users.register"))

    return render_template(
        "users/home.html",
        page_title="Home",
        user=user
    )


@auth_decorator
@bp.route("/rooms/create", methods=["POST"])
def rooms_create():
    crsid = auth_decorator.principal
    user = User.query.filter_by(crsid=crsid).first()

    errors = {}
    keys = ("room_name",)
    values = get_form_values(request, keys)

    if len(values["room_name"]) <= 1:
        errors["room_name"] = "That name is too short."

    if errors:
        flash("There were errors with the information you provided", "error")
        return render_template(
            "users/home.html",
            user=user,
            page_title="Home",
            errors=errors,
            **values,
        )
    else:

        try_id = gen_room_id(auth_decorator.principal)
            
        # this might be expensive and unnecessary
        while Room.query.filter_by(id=try_id).first():
            try_id = gen_room_id(auth_decorator.principal)

        new_room = Room(
            id=try_id,
            name=values["room_name"],
            attendee_pw=gen_unique_string(),
            moderator_pw=gen_unique_string(),
            authentication=Authentication.PUBLIC,
            password=gen_unique_string()[0:6],
        )

        new_room.whitelisted_users.append(user)
        user.rooms.append(new_room)
        db.session.commit()
        current_app.logger.info(f"User { crsid } created room {values['room_name']}")
        flash("Created room successfully", "success")
        return redirect(url_for("users.home"))


@bp.route("/register_group", methods=("GET", "POST"))
@auth_decorator
def register_group():
    crsid = auth_decorator.principal

    user = User.query.filter_by(crsid=crsid).first()

    # Check the user is registered with us, if not redirect to the user reg page
    if not user:
        return redirect(url_for("users.register"))

    if request.method == "POST":

        values = {}
        for key in ("group_name", "group_short_name"):
            values[key] = request.form.get(key, "").strip()

        errors = {}

        if len(values["group_name"]) <= 1:
            errors["group_name"] = "That name is too short."

        is_valid_short_name = validate_short_name(values["group_short_name"])
        if not is_valid_short_name:
            errors["group_short_name"] = _(
                "Your short name must be a single word and have fewer than 12 characters."
            )

        id = values["group_short_name"].lower()

        if Group.query.filter_by(id=id).first():
            errors["group_short_name"] = _("Short name is already in use.")

        if errors:
            return render_template(
                "users/register_group.html",
                page_title=_("Create your group"),
                user=user,
                errors=errors,
                **values,
            )
        else:
            group = Group(
                id=id,
                name=values["group_name"],
            )

            db.session.add(group)
            db.session.commit()

            user.groups.append(group)
            db.session.commit()

            current_app.logger.info(f"User { crsid } registered group {id}")

            return redirect(url_for("users.home"))

    else:
        return render_template(
            "users/register_group.html",
            page_title=_("Create your group"),
            user=user,
            errors={},
        )


@bp.route("/register", methods=("GET", "POST"))
@auth_decorator
def register():

    crsid = auth_decorator.principal

    existing_user = User.query.filter_by(crsid=crsid).first()

    if existing_user:

        # If the User is a visitor, upgrade them to being a user
        if existing_user.role == RoleType.VISITOR:
            existing_user.role = RoleType.USER
            current_app.logger.info(f"Changed role of user '{ user.name }' from visitor to user.")
            db.session.commit()

        return redirect(url_for("users.home"))

    if request.method == "POST":

        # Input validation from https://github.com/SRCF/control-panel/blob/master/control/webapp/signup.py#L37

        values = {}
        for key in ("full_name", "email_address"):
            values[key] = request.form.get(key, "").strip()

        for key in ("dpa", "tos"):
            values[key] = bool(request.form.get(key, False))

        errors = {}

        if len(values["full_name"]) <= 1:
            errors["full_name"] = "A name is required."

        email_err = validate_email(crsid, values["email_address"])
        if email_err is not None:
            errors["email_address"] = email_err

        if not values["dpa"]:
            errors["dpa"] = "We need to store your information to register you."
        if not values["tos"]:
            errors["tos"] = "You must accept the terms of service to register."

        if User.query.filter_by(email=values["email_address"]).first():
            errors["email_address"] = "That email address is already registered."

        if errors:
            return render_template(
                "users/register.html",
                page_title="Register",
                crsid=crsid,
                errors=errors,
                **values,
            )
        else:

            user = User(
                email=values["email_address"],
                full_name=values["full_name"],
                crsid=auth_decorator.principal,
                role=Role.query.filter_by(role=RoleType("user")).first(),
            )

            try_id = gen_room_id(auth_decorator.principal)
            
            # this might be expensive and unnecessary
            while Room.query.filter_by(id=try_id).first():
                try_id = gen_room_id(auth_decorator.principal)

            home_room = Room(
                id=try_id,
                name="Home room",
                attendee_pw=gen_unique_string(),
                moderator_pw=gen_unique_string(),
                authentication=Authentication.PUBLIC,
                password=gen_unique_string()[0:6],
            )

            home_room.whitelisted_users.append(user)
            user.rooms.append(home_room)

            db.session.add(user)
            db.session.commit()

            current_app.logger.info(
                f"Registered user with CRSid {auth_decorator.principal}"
            )

            return redirect(url_for("users.home"))

    else:

        signups = Setting.query.filter_by(name="enable_signups").first()
        if signups.enabled:
            # defaults
            lookup_data = fetch_lookup_data(crsid)
            values = {
                "full_name": lookup_data["name"],
                "email_address": lookup_data["email"],
                "crsid": crsid,
                "dpa": False,
                "tos": False,
            }

            return render_template(
                "users/register.html",
                page_title="Register",
                errors={},
                **values
            )

        else:
            return render_template(
                "users/no_signup.html", page_title="Signups are not available",
            )


@bp.route("/user", methods=("GET", "POST"))
@auth_decorator
def profile():
    crsid = auth_decorator.principal
    user = User.query.filter_by(crsid=crsid).first()

    # Check the user is registered with us, if not redirect to the user reg page
    if not user:
        return redirect(url_for("users.register"))

    return render_template(
        "users/profile.html",
        user=user,
        page_title="Profile",
        page_parent=url_for("users.home"),
    )


@bp.route("/update", methods=["POST"])
def update():
    res = request.get_json(force=True)
    crsid = auth_decorator.principal
    user = User.query.filter_by(crsid=crsid).first()
    error = False
    if res["type"] == "email":
        email_err = validate_email(crsid, res["value"])
        if email_err is not None:
            error = True
            flash(email_err, "error")
    if not error:
        old_field = getattr(user, res["type"])
        setattr(user, res["type"], res["value"])
        current_app.logger.info(
            f"Changing {res['type']} for {auth_decorator.principal} from {old_field} to {res['value']}"
        )
        db.session.commit()
        flash("Your profile was updated successfully", "success")
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


@bp.route("/update_error", methods=["POST"])
def update_error():
    if request.method == "POST":
        error = request.get_json(force=True)
        if error["code"]:
            flash("User profile was not updated successfully", "error")
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}

