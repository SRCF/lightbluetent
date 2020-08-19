from flask import Blueprint, render_template, request, flash
from lightbluetent.models import db, Society

bp = Blueprint("society", __name__, url_prefix="/s")

@bp.route("/<uid>")
def welcome(uid):

    society = Society.query.filter_by(uid=uid).first()

    return render_template("society/welcome.html", page_title=f"Home page for { society.name }", society=society)
