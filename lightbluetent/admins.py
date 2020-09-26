from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    session,
    url_for,
    redirect,
    abort,
    current_app,
)

bp = Blueprint("admins", __name__, url_prefix="/admin")

@bp.route("/<uid>", methods=("GET", "POST"))
def manage(uid):
    render_template("admins/index.html")
