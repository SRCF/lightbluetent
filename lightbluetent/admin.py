import re

from flask import Blueprint, render_template, request, flash, abort, redirect, url_for
from lightbluetent.models import db, User, Society
from lightbluetent.utils import auth_decorator, validate_email

ILLEGAL_NAME_RE = re.compile(r'[:,=\n]')
ILLEGAL_NAME_ERR = "Please do not use any of the following characters: : , = ⏎ "

bp = Blueprint("admin", __name__, url_prefix="/admin")

@auth_decorator
@bp.route("/<short_name>", methods=("GET", "POST"))
def admin(short_name):

    current_crsid = auth_decorator.principal

    # TODO: at the moment, it is possible that a User's CRSid is not unique, and so
    # using first() here may return the wrong value, giving 403 responses when that
    # User is an administrator. This will be fixed when the requirement for a unique
    # CRSid is added to the registeration form (not implemented at the moment for ease
    # of testing).
    current_user = User.query.filter_by(crsid=current_crsid).first()

    # Redirect to the registration page if the authenticated user isn't registered
    if not current_user:
        return redirect(url_for("home.register"))

    current_user_socs = current_user.societies

    # Check the society exists
    society = Society.query.filter_by(uid=short_name).first()
    if not society:
        abort(404)
    # Check that the currently authenticated user is allowed to administer this society.
    if not society in current_user_socs:
        abort(403)

    society_admins = society.admins

    if request.method == "POST":

        values = {}
        for key in ("soc_name", "soc_short_name", "website", "description",
                    "welcome_text", "logo", "banner_text", "banner_color",
                    "mute_on_start", "disable_private_chat"):
            values[key] = request.form.get(key, "").strip()

        errors = {}

        if len(values["soc_name"]) < 1:
            errors["soc_name"] = "Society name is too short."
        if len(values["soc_short_name"]) < 1:
            errors["soc_short_name"] = "Society short name is too short."

        # TODO: validate and process the logo

        # TODO: tweak these values when their ideal maximum lengths become apparent
        if len(values["welcome_text"]) > 100:
            errors["welcome_text"] = "Welcome text is too long."
        if len(values["banner_text"]) > 100:
            errors["banner_text"] = "Banner text is too long."

        uid = values["soc_short_name"].lower()
        if Society.query.filter_by(uid=uid).first():
            errors["soc_short_name"] = "That society short name is already in use."

        if errors:
            return render_template("admin/admin.html", page_title=f"Administration page for { society.short_name }",
                                   short_name=short_name, errors=errors, admins=society_admins, **values)
        else:
            society.name = values["soc_name"]
            society.short_name = values["soc_short_name"]
            society.website = values["website"]
            society.description = values["description"]
            society.welcome_text = values["welcome_text"]
            society.logo = values["logo"]
            society.banner_text = values["banner_text"]
            society.banner_color = values["banner_color"]
            society.mute_on_start = values["mute_on_start"]
            society.disable_private_chat = values["disable_private_chat"]

            db.session.commit()

            return redirect(url_for(admin.admin))

    else:
        # current values
        values = {
            "soc_name": society.name,
            "soc_short_name": society.short_name,
            "website": society.website,
            "description": society.description,
            "welcome_text": society.welcome_text,
            "logo": society.logo,
            "banner_text": society.banner_text,
            "banner_color": society.banner_color,
            "mute_on_start": society.mute_on_start,
            "disable_private_chat": society.disable_private_chat
        }

        return render_template("admin/admin.html", page_title=f"Administration page for { society.short_name }",
                               short_name=short_name, errors={}, admins=society_admins, **values)

@auth_decorator
@bp.route("/<short_name>/add", methods=("GET", "POST"))
def add(short_name):
    current_crsid = auth_decorator.principal
    current_user = User.query.filter_by(crsid=current_crsid).first()
    current_user_socs = current_user.societies

    # Check the society exists
    society = Society.query.filter_by(uid=short_name).first()
    society_admins = society.admins
    if not society:
        abort(404)
    # Check that the currently authenticated user is allowed to administer this society.
    if not society in current_user_socs:
        abort(403)

    if request.method == "POST":

        values = {}

        for key in ("first_name", "surname", "email_address", "crsid"):
            values[key] = request.form.get(key, "").strip()

        errors = {}

        # If the user being added is already registered, then simply get that
        # add this society to that user's list of societies

        # TODO: identifying users should be CRSid-based, changed to email address for testing purposes
        existing_user = User.query.filter_by(email=values["email_address"]).first()
        if existing_user:
            print("Already registered.")
            # Check the existing user isn't already an admin
            if not society in existing_user.societies:
                pass
            else:
                errors["crsid"] = "This user is already an administrator."

            # Check that the values we already have have been given by the registrant.
            if existing_user.first_name != values["first_name"]:
                errors["first_name"] = "This CRSid is already registered, but not under this name. Please use the user's registered name."
            if existing_user.surname != values["surname"]:
                errors["surname"] = "This CRSid is already registered, but not under this name. Please use the user's registered name."
            if existing_user.email != values["email_address"]:
                errors["email_address"] = "This CRSid is already registered, but not under this email address. Please use the user's registered email address."

            if errors:
                return render_template("admin/admin_add.html", page_title=f"Add an administrator to { society.short_name }",
                                       errors=errors, admins=society_admins, **values)
            else:
                existing_user.societies.append(society)
                db.session.commit()
                return redirect(url_for("admin.admin", short_name=short_name))

        # Otherwise, we'll need to add a new User
        else:
            print("Not already registered.")
            if len(values["first_name"]) <= 1:
                errors["first_name"] = "A first name is required."
            elif ILLEGAL_NAME_RE.search(values["first_name"]):
                errors["first_name"] = ILLEGAL_NAME_ERR

            email_err = validate_email(values["crsid"], values["email_address"])
            if email_err is not None:
                errors["email_address"] = email_err

            if errors:
                return render_template("admin/admin_add.html", page_title=f"Add an administrator to { society.short_name }",
                                       errors=errors, admins=society_admins, **values)
            else:
                new_user = User(email=values["email_address"],
                                first_name=values["first_name"],
                                surname=values["surname"],
                                crsid=values["crsid"])
                new_user.societies.append(society)

                print(new_user)
                db.session.add(new_user)
                db.session.commit()

                return redirect(url_for("admin.admin", short_name=short_name))

    else:
        # default values
        values = {
            "first_name": "",
            "surname": "",
            "email_address": "",
            "crsid": ""
        }

        return render_template("admin/admin_add.html", page_title=f"Add an administrator to { society.short_name }",
                               errors={}, admins=society_admins, **values)
