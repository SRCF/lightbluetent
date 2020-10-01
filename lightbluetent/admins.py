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
from lightbluetent.users import auth_decorator
from lightbluetent.models import db, Setting, User, Group


bp = Blueprint("admins", __name__, url_prefix="/admin")

@auth_decorator
@bp.route("/", methods=("GET", "POST"))
def manage():
    crsid = auth_decorator.principal
    user = User.query.filter_by(crsid=crsid).first()

    if not user:
        return redirect(url_for("users.register"))

    # TO-DO: PAGINATION
    if user.role.name == "admin":
        return render_template(
            "admins/index.html",
            page_title="Administrator panel",
            settings=Setting.query.all(),
            groups=Group.query.all(),
            user=user
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
            flash("Site setting updated successfully", 'success')
        else:
            flash("Error occurred when finding entry in database", 'error')
        return json.dumps({"success": True}), 200, {"ContentType": "application/json"}

@bp.route("/update_setting_error", methods=["POST"])
def update_setting_error():
    if request.method == "POST":
        error = request.get_json(force=True)
        if error["code"]:
            flash("Site setting was not updated successfully", 'error')
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}
