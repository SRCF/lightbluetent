from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    url_for,
    redirect,
    abort,
    current_app,
)
import json
from datetime import datetime
from lightbluetent.users import auth_decorator
from lightbluetent.models import db, Setting, User, Group
from lightbluetent.config import PermissionType


bp = Blueprint("admins", __name__, url_prefix="/admin")


@auth_decorator
@bp.route("/", methods=("GET", "POST"))
def manage():
    crsid = auth_decorator.principal
    user = User.query.filter_by(crsid=crsid).first()

    if not user:
        return redirect(url_for("users.register"))

    # TO-DO: PAGINATION
    if user.has_permission_to(PermissionType.CAN_VIEW_ADMIN_PAGE):
        return render_template(
            "admins/index.html",
            page_title="Administrator panel",
            groups=Group.query.all(),
            user=user,
        )
    else:
        abort(404)


@bp.route("/update_setting", methods=["POST"])
def update_setting():
    setting = request.get_json(force=True)
    db_setting = Setting.query.filter_by(name=setting["name"]).first()
    if db_setting:
        db_setting.enabled = setting["enabled"]
        db_setting.updated_at = datetime.now()
        db.session.commit()
        current_app.logger.info(f"Updated site setting {db_setting} with value {setting["enabled"]}")
        flash("Site setting updated successfully", "success")
    else:
        flash("Error occurred when finding entry in database", "error")
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


@bp.route("/update_setting_error", methods=["POST"])
def update_setting_error():
    error = request.get_json(force=True)
    if error["code"]:
        flash("Site setting was not updated successfully", "error")
        current_app.logger.error(f"Got error with code {json.dumps(error)})
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}
