import re

from flask import Blueprint, render_template, request, flash, session, url_for, redirect, abort
from lightbluetent.models import db, User, Society
from lightbluetent.utils import gen_unique_string, validate_email
from datetime import datetime

import ucam_webauth
import ucam_webauth.raven
import ucam_webauth.raven.flask_glue

bp = Blueprint("home", __name__)

auth_decorator = ucam_webauth.raven.flask_glue.AuthDecorator(desc="SRCF Lightbluetent")

@bp.route("/")
def index():
    return render_template("home/index.html", page_title="Welcome to the 2020 Virtual Freshers' Fair!")

@bp.route("/logout")
def logout():
    auth_decorator.logout()
    return redirect(url_for("home.index"))

@bp.route("/log_in")
@auth_decorator
def log_in():
    return redirect(url_for("home.home"))

@bp.route("/home")
@auth_decorator
def home():
    crsid = auth_decorator.principal

    user = User.query.filter_by(crsid=crsid).first()

    if not user:
        return redirect(url_for("home.register"))

    if user.societies:
        user_societies = user.societies

        return render_template("home/home.html", page_title="Home", user_societies=user_societies, crsid=crsid)

    else:
        return render_template("home/home.html", page_title="Home", user_societies={}, crsid=crsid)



@bp.route("/register_soc", methods=("GET", "POST"))
@auth_decorator
def register_soc():
    crsid = auth_decorator.principal

    user = User.query.filter_by(crsid=crsid).first()

    # Check the user is registered with us, if not redirect to the user reg page
    if not user:
        return redirect(url_for("home.register"))

    if request.method == "POST":

        values = {}
        for key in ("soc_name", "soc_short_name"):
            values[key] = request.form.get(key, "").strip()

        errors = {}

        values["uid"] = values["soc_short_name"].lower()
        values["bbb_id"] = gen_unique_string()
        values["moderator_pw"] = gen_unique_string()[0:12]
        values["attendee_pw"] = gen_unique_string()[0:12]

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

        if Society.query.filter_by(uid=values["uid"]).first():
            errors["soc_short_name"] = "That society short name is already in use."

        if errors:
            return render_template("home/register_soc.html", page_title="Register a society", crsid=crsid, errors=errors, **values)
        else:
            society = Society(short_name=values["soc_short_name"],
                              name=values["soc_name"],
                              attendee_pw=values["attendee_pw"],
                              moderator_pw=values["moderator_pw"],
                              uid=values["uid"],
                              bbb_id=values["bbb_id"])

            db.session.add(society)
            db.session.commit()

            user.societies.append(society)
            db.session.commit()

            return redirect(url_for("home.home"))


    else:
        return render_template("home/register_soc.html", page_title="Register a society", crsid=crsid, errors={})


@bp.route("/register", methods=("GET", "POST"))
@auth_decorator
def register():

    crsid = auth_decorator.principal

    existing_user = User.query.filter_by(crsid=crsid).first()
    if existing_user:
        return redirect(url_for("home.home"))

    if request.method == "POST":

        # Input validation from https://github.com/SRCF/control-panel/blob/master/control/webapp/signup.py#L37

        values = {}
        for key in ("first_name", "surname", "email_address"):
            values[key] = request.form.get(key, "").strip()

        for key in ("dpa", "tos"):
            values[key] = bool(request.form.get(key, False))

        errors = {}

        if len(values["first_name"]) <= 1:
            errors["first_name"] = "A first name is required."

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
            return render_template("home/register.html", page_title="Register", crsid=crsid, errors=errors, **values)
        else:

            user = User(email=values["email_address"],
                         first_name=values["first_name"],
                         surname=values["surname"],
                         crsid=auth_decorator.principal)

            db.session.add(user)
            db.session.commit()

            return redirect(url_for("home.home"))

    else:
        # defaults
        values = {
            "first_name": "",
            "surname": "",
            "email_address": "",
            "dpa": False,
            "tos": False
        }

        return render_template("home/register.html", page_title="Register",
                           crsid=crsid, errors={}, **values)

