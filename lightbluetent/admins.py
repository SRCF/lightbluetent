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
from PIL import Image, UnidentifiedImageError


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


@bp.route("/update/<update_type>", methods=["POST"])
def update(update_type):
    setting = request.get_json()
    db_setting = Setting.query.filter_by(name=setting["name"]).first()
    if not db_setting:
        flash("Error occurred when finding entry in database", "error")
        return json.dumps({"success": False}), 404, {"ContentType": "application/json"}

    errors = {}

    if update_type == "toggle_setting":
        db_setting.enabled = setting["enabled"]

    elif update_type == "site_cover":
        cover = request.files.get("logo")
        if cover:
            try:
                assert cover.filename != ""
                cover_img = Image.open(cover)
            except (AssertionError, UnidentifiedImageError):
                errors["site_cover"] = "Invalid file."
            else:
                if not db_setting.delete_cover():
                    abort(500)

                safe_gid = path_sanitise(group.id)
                static_filename = lambda v: (
                    safe_gid + v + "_" + gen_unique_string() + ".png"
                )

                images_dir = current_app.config["IMAGES_DIR"]

                current_app.logger.info(
                    f"Changing logo for user { crsid }, group { group.id }..."
                )

                if not os.path.isdir(images_dir):
                    current_app.logger.error(f"'{ images_dir }': no such directory.")
                    abort(500)

                key = f"logo:{group.id}"
                success = False

                for dpi, img in resize_image(
                    logo_img, current_app.config["MAX_LOGO_SIZE"]
                ):
                    variant = f"@{dpi}x"
                    subpath = static_filename(variant)
                    path = os.path.join(images_dir, subpath)
                    img.save(path)

                    variant = Asset(key=key, variant=variant, path=subpath)
                    db.session.add(variant)
                    current_app.logger.info(
                        f"For id={group.id!r}: saved new logo variant [{variant!r}] {path!r}"
                    )
                    success = True

                if not success:
                    errors["logo"] = "Failed to resize image."

                else:
                    current_app.logger.info(f"Saved new logo for group '{ group.id }'")
                    group.logo = key
                    db.session.commit()
    else:
        current_app.logger.error(
            f"Attempted to update room page at incorrect endpoint: {update_type}"
        )
    
    db_setting.updated_at = datetime.now()
    db.session.commit()
    current_app.logger.info(f"Updated site setting {db_setting}")
    flash("Site setting updated successfully", "success")
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


@bp.route("/update_setting_error", methods=["POST"])
def update_setting_error():
    error = request.get_json(force=True)
    if error["code"]:
        flash("Site setting was not updated successfully", "error")
        current_app.logger.error(f"Got error with code {json.dumps(error)}")
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}
