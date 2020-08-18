from flask import Blueprint, render_template, request, flash
from lightbluetent.models import db

bp = Blueprint("society", __name__, url_prefix="/s")

@bp.route("/<socname>")
def society_welcome(socname):
    return render_template("home/welcome.html", socname=socname)