from flask import Blueprint, render_template

bp = Blueprint("admin", __name__, url_prefix="/admin")

@bp.route("/<socname>")
def admin(socname):
    return render_template("admin/admin.html", socname=socname)
