from flask import Blueprint, render_template, request, flash
from lightbluetent.models import db

bp = Blueprint("admin", __name__, url_prefix="/admin")

@bp.route("/<short_name>", methods=("GET", "POST"))
def admin(short_name):
    if request.method == "POST":

        name =                 request.form["name"]
        new_short_name =       request.form["short_name"]
        website =              request.form["website"]
        description =          request.form["description"]
        welcome_text =         request.form["welcome_text"]
        logo =                 request.form["logo"]
        banner_text =          request.form["banner_text"]
        banner_color =         request.form["banner_color"]
        mute_on_start =        request.form["mute_on_start"]
        disable_private_chat = request.form["disable_private_chat"]

        errors = []

        if not name:
            errors.append("A society name is required.")
        if not new_short_name:
            errors.append("A short society name is required.")

        # TODO: confirm new_short_name is unique

        if not errors:
            pass
            # TODO: write to the database
        else:
            for message in errors:
                flash(message)


    # TODO: pre-fill fields with current values depending on the authenticated user
    return render_template("admin/admin.html", short_name=short_name, page_title=f"Administration page for { short_name }")
