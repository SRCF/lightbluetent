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
import json
from datetime import datetime
from lightbluetent.home import auth_decorator
from lightbluetent.models import db, Setting, User


bp = Blueprint("admins", __name__, url_prefix="/admin")


@bp.route("/", methods=("GET", "POST"))
def manage():
    crsid = auth_decorator.principal
    user = User.query.filter_by(crsid=crsid).first()

    if not user:
        return redirect(url_for("home.register"))

    if user.role.permission.name == "admin":
        return render_template(
            "admins/index.html",
            page_title="Administrator panel",
            settings=Setting.query.all(),
        )
    else:
        abort(404)


@bp.route("/update_setting", methods=["POST"])
def update_setting():
    if request.method == "POST":
        setting = request.get_json(force=True)
        db_setting = Setting.query.filter_by(name=setting["name"]).first()
        if db_setting:
            db_setting.enabled = setting["enabled"]
            db_setting.updated_at = datetime.now()
            db.session.commit()
            flash("Site setting updated successfully")
        else:
            flash("Error occurred when finding entry in database")
        return json.dumps({"success": True}), 200, {"ContentType": "application/json"}

@bp.route("/update_setting_error", methods=["POST"])
def update_setting_error():
    if request.method == "POST":
        error = request.get_json(force=True)
        if error["code"]:
            flash(u"Site setting was not updated successfully", 'error')
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}
