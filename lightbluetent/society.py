import re

from flask import Blueprint, render_template, request, flash, abort, current_app
from lightbluetent.models import db, Society

bp = Blueprint("society", __name__, url_prefix="/s")

email_re = re.compile(r"^\S+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+$")

@bp.route("/<uid>")
def welcome(uid):

    society = Society.query.filter_by(uid=uid).first()

    if not society:
        return abort(404)

    desc_paragraphs = {}
    # Split the description into paragraphs so it renders nicely.
    if society.description is not None:
        desc_paragraphs=society.description.split("\n")

    sessions_data = {"days": current_app.config["NUMBER_OF_DAYS"]}    

    return render_template("society/welcome.html", page_title=f"{ society.name }",
                           society=society, desc_paragraphs=desc_paragraphs,
                           sessions_data=sessions_data)
