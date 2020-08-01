from flask import Blueprint, render_template

bp = Blueprint("admin", __name__)

@bp.route("/admin/<socname>")
def admin (socname):
    return render_template("admin/admin.html", socname=socname)
