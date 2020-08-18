import re

from flask import Blueprint, render_template, request, flash, session, url_for, redirect, abort
from lightbluetent.models import db, User, Society
from lightbluetent.utils import gen_unique_string, validate_email, auth_decorator
from datetime import datetime

ILLEGAL_NAME_RE = re.compile(r'[:,=\n]')
ILLEGAL_NAME_ERR = "Please do not use any of the following characters: : , = ⏎ "

bp = Blueprint("home", __name__)

@bp.route("/")
def index():
    return render_template("home/index.html")

@bp.route("/logout")
def logout():
    auth_decorator.logout()
    flash("You have been logged out.")
    return redirect(url_for("home.index"))

@bp.route("/register", methods=("GET", "POST"))
@auth_decorator
def register():

    crsid = auth_decorator.principal

    if request.method == "POST":

        # Input validation from https://github.com/SRCF/control-panel/blob/master/control/webapp/signup.py#L37

        # TODO: CRSid field should be unique, i.e. one User per user.
        # Will want to do this later because it'll make testing a pain...

        values = {}
        for key in ("first_name", "surname", "email_address", "soc_name", "soc_short_name"):
            values[key] = request.form.get(key, "").strip()

        for key in ("dpa", "tos"):
            values[key] = bool(request.form.get(key, False))

        errors = {}

        if len(values["first_name"]) <= 1:
            errors["first_name"] = "A first name is required."
        elif ILLEGAL_NAME_RE.search(values["first_name"]):
            errors["first_name"] = ILLEGAL_NAME_ERR

        email_err = validate_email(crsid, values["email_address"])
        if email_err is not None:
            errors["email_address"] = email_err

        if not values["dpa"]:
            errors["dpa"] = "We need to store your information to register you."
        if not values["tos"]:
            errors["tos"] = "You must accept the terms of service to register."

        values["uid"] = values["soc_short_name"].lower()
        values["bbb_id"] = gen_unique_string()
        values["moderator_pw"] = gen_unique_string()[0:12]
        values["attendee_pw"] = gen_unique_string()[0:12]

        if User.query.filter_by(email=values["email_address"]).first():
            errors["email_address"] = "That email address is already registered."
        if Society.query.filter_by(uid=values["uid"]).first():
            errors["soc_short_name"] = "That society short name is already in use."

        # TODO: What's the best way of handling the (unlikely) event
        #       that the passwords are:
        #    a) non-unique across registered societies
        #    b) the same
        #       Currently we abort(500)

        if values["moderator_pw"] == values["attendee_pw"]:
            abort(500)

        elif (Society.query.filter_by(attendee_pw=values["attendee_pw"]).first()
                or Society.query.filter_by(moderator_pw=values["moderator_pw"]).first()
                or Society.query.filter_by(bbb_id=values["bbb_id"]).first()):
            abort(500)

        if errors:
            return render_template("home/register.html", page_title="Register a society", errors=errors, **values)
        else:
            admin = User(email=values["email_address"],
                         first_name=values["first_name"],
                         surname=values["surname"],
                         crsid=auth_decorator.principal)

            society = Society(short_name=values["soc_short_name"],
                              name=values["soc_name"],
                              attendee_pw=values["attendee_pw"],
                              moderator_pw=values["moderator_pw"],
                              uid=values["uid"],
                              bbb_id=values["bbb_id"])

            society.admins.append(admin)

            db.session.add(admin)
            db.session.add(society)
            db.session.commit()

            return redirect(url_for("home.register_success"))

    else:
        # defaults
        values = {
            "first_name": "First name from lookup",
            "surname": "Surname from lookup",
            "email_address": "Email address from lookup",
            "dpa": False,
            "tos": False
        }

        return render_template("home/register.html", page_title="Register a Society",
                           crsid=crsid, errors={}, **values)
      
            return redirect(url_for("society", socname=soc_short_name))

        else:
            for message in errors:
                flash(message)

@bp.route("/register/success")
def register_success():
    return render_template("home/register_success.html", page_title="Success!")