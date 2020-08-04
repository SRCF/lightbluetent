from flask import Blueprint, render_template, request, flash, session, url_for, redirect
from lightbluetent.models import db, User, Society
from lightbluetent.utils import gen_unique_string
from datetime import datetime

import ucam_webauth
import ucam_webauth.raven
import ucam_webauth.raven.flask_glue

bp = Blueprint("home", __name__)

auth_decorator = ucam_webauth.raven.flask_glue.AuthDecorator(desc="SRCF Lightbluetent")

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
    if request.method == "POST":
        name = request.form["name"]
        email_address = request.form["email_address"]
        soc_name = request.form["soc_name"]
        soc_short_name = request.form["soc_short_name"]
        uid = soc_short_name.lower()
        bbb_id = gen_unique_string()
        moderator_pw = gen_unique_string()[0:12]
        attendee_pw = gen_unique_string()[0:12]

        errors = []

        if not name:
            errors.append("A name is required.")
        if not email_address:
            errors.append("An email address is required.")
        if not "@" in email_address:
            errors.append("Enter a valid email address.")
        elif not "." in email_address:
            errors.append("Enter a valid email address.")
        if not soc_name:
            errors.append("A society name is required.")
        if not soc_short_name:
            errors.append("A short society name is required.")

        # TODO: What's the best way of handling the (unlikely) event
        #       that the passwords are:
        #    a) non-unique across registered societies
        #    b) the same
        #       Currently we flash the error:
        #       "An error occured. Please try again."

        if moderator_pw == attendee_pw:
            errors.append("An error occured. Please try again.")

        if User.query.filter_by(email=email_address):
            errors.append("That email address is already registered.")
        if Society.query.filter_by(uid=uid):
            errors.append("That society short name is already in use.")
        elif (Society.query.filter_by(attendee_pw=attendee_pw)
                or Society.query.filter_by(moderator_pw=moderator_pw)
                or Society.query.filter_by(bbb_id=bbb_id)):
            errors.append("An error occured. Please try again.")


        if not errors:

            # TODO: BBB create() API call goes here?

            admin = User(email=email_address,
                         name=name,
                         society_id=society.id,
                         crsid=auth_decorator.principal)

            society = Society(short_name=soc_short_name,
                              name=name,
                              attendee_pw=attendee_pw,
                              moderator_pw=moderator_pw,
                              uid=uid,
                              bbb_id=bbb_id,
                              admins=admin)

            db.session.add(society)
            db.session.add(admin)
            db.session.commit()

        else:
            for message in errors:
                flash(message)

    print(f"{auth_decorator.principal}")

    return render_template("home/register.html", page_title="Register a Society",
                           crsid=auth_decorator.principal)

@bp.route("/<socname>")
def society_welcome(socname):
    return render_template("home/welcome.html", socname=socname)
