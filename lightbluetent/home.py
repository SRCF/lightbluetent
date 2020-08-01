from flask import Blueprint, render_template, request, flash
from lightbluetent.models import db, User, Society

bp = Blueprint("home", __name__)

@bp.route("/")
def index():
    return render_template("home/index.html")

@bp.route("/login")
def login():
    return render_template("home/login.html")

@bp.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        name = request.form["name"]
        email_address = request.form["email_address"]
        soc_name = request.form["soc_name"]
        soc_short_name = request.form["soc_short_name"]

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

        if not errors:
            pass
            # TODO: write to the database
        else:
            for message in errors:
                flash(message)

    return render_template("home/register.html", page_title="Register a Society")

@bp.route("/<socname>")
def society_welcome(socname):
    return render_template("home/welcome.html", socname=socname)
