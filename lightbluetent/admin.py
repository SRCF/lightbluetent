import os

from flask import Blueprint, render_template, request, flash, abort, redirect, url_for, current_app
from lightbluetent.models import db, User, Society
from lightbluetent.home import auth_decorator
from lightbluetent.utils import gen_unique_string
from PIL import Image

bp = Blueprint("admin", __name__, url_prefix="/admin")

LOGO_ALLOWED_EXTENSIONS = {".png", ".jpeg", ".jpg", ".gif"}

# Delete logo on disk for the society with given uid
def delete_society_logo(uid):

    society = Society.query.filter_by(uid=uid).first()
    logo_path = f"images/{ society.logo }"

    if society.logo == "default_logo.png":
        return
    else:
        old_logo = os.path.join(current_app.root_path, "static/images", society.logo)
        os.remove(old_logo)

        society.logo = "default_logo.png"
        db.session.commit()

        return

# Delete logo on disk for the society with given uid
def delete_society_bbb_logo(uid):
    society = Society.query.filter_by(uid=uid).first()
    logo_path = f"images/{ society.bbb_logo }"

    if society.bbb_logo == "default_bbb_logo.png":
        return
    else:
        old_logo = os.path.join(current_app.root_path, "static/images", society.bbb_logo)
        os.remove(old_logo)

        society.bbb_logo = "default_bbb_logo.png"
        db.session.commit()

        return



@bp.route("/<uid>", methods=("GET", "POST"))
@auth_decorator
def admin(uid):

    society = Society.query.filter_by(uid=uid).first()

    if not society:
        abort(404)

    crsid = auth_decorator.principal
    user = User.query.filter_by(crsid=crsid).first()

    if society not in user.societies:
        abort(403)

    if request.method == "POST":

        # Input validation from https://github.com/SRCF/control-panel/blob/master/control/webapp/signup.py#L37

        values = {}

        for key in ("soc_name", "website", "description",
                    "welcome_text", "logo", "banner_text", "banner_color", "new_admin_crsid"):
            values[key] = request.form.get(key, "").strip()

        for key in ("mute_on_start", "disable_private_chat"):
            values[key] = bool(request.form.get(key, False))

        errors = {}

        if len(values["soc_name"]) <= 1:
            errors["soc_name"] = "Society name is too short."

        if "logo" in request.files:
            logo = request.files["logo"]
            bbb_logo = request.files["bbb_logo"]

            logo_filename, logo_extension = os.path.splitext(logo.filename)
            bbb_logo_filename, bbb_logo_extension = os.path.splitext(bbb_logo.filename)

            # TODO: is use of current_app.root_path okay?
            if logo and logo_filename != "":
                if logo_extension in LOGO_ALLOWED_EXTENSIONS:

                    # Delete the old logo if it's not the default
                    delete_society_logo(uid)

                    static_filename = society.uid + "_" + gen_unique_string() + logo_extension
                    path = os.path.join(current_app.root_path, "static/images", static_filename)

                    logo_img = Image.open(logo)
                    logo_resized = logo_img.resize((512, 512))
                    logo_resized.save(path)

                    society.logo = static_filename
                    db.session.commit()
                else:
                    errors["logo"] = "Invalid file."

            if bbb_logo and bbb_logo_filename != "":
                if bbb_logo_extension in LOGO_ALLOWED_EXTENSIONS:

                    # Delete the old logo if it's not the default
                    delete_society_bbb_logo(uid)

                    static_filename = society.uid + "_bbb_" + gen_unique_string() + bbb_logo_extension
                    path = os.path.join(current_app.root_path, "static/images", static_filename)

                    bbb_logo_img = Image.open(bbb_logo)
                    bbb_logo_resized = bbb_logo_img.resize((512, 256))
                    bbb_logo_resized.save(path)

                    society.bbb_logo = static_filename
                    db.session.commit()
                else:
                    errors["bbb_logo"] = "Invalid file."

        # TODO: tweak these values when their ideal maximum lengths become apparent
        if len(values["welcome_text"]) > 100:
            errors["welcome_text"] = "Welcome text is too long."
        if len(values["banner_text"]) > 100:
            errors["banner_text"] = "Banner text is too long."

        # Adding a new admin
        if values["new_admin_crsid"] != "":

            new_admin = User.query.filter_by(crsid=values["new_admin_crsid"]).first()
            if not new_admin:
                errors["new_admin_crsid"] = "That user is not registered yet. Users must register before being added as administrators."
            else:
                society.admins.append(new_admin)

        if errors:
            return render_template("admin/admin.html",
                                   page_title=f"Settings for { society.name }",
                                   society=society, crsid=crsid, errors=errors, **values)
        else:
            society.name = values["soc_name"]
            society.website = values["website"] if society.website != "None" else ""
            society.description = values["description"] if society.description != "None" else ""
            society.welcome_text = values["welcome_text"] if society.welcome_text != "None" else ""
            society.banner_text = values["banner_text"] if society.banner_text != "None" else ""
            society.banner_color = values["banner_color"]
            society.mute_on_start = values["mute_on_start"]
            society.disable_private_chat = values["disable_private_chat"]

            db.session.commit()

            return redirect(url_for("home.home"))

    else:
        # defaults
        values = {
            "soc_name": society.name,
            "website": society.website if society.website != "None" else "",
            "description": society.description if society.description != "None" else "",
            "welcome_text": society.welcome_text if society.welcome_text != "None" else "",
            "banner_text": society.banner_text if society.banner_text != "None" else "",
            "banner_color": society.banner_color,
            "logo": society.logo,
            "mute_on_start": society.mute_on_start,
            "disable_private_chat": society.disable_private_chat
        }

    return render_template("admin/admin.html",
                           page_title=f"Settings for { society.name }",
                           society=society, crsid=crsid, errors={}, **values)

@bp.route("/<uid>/delete_logo")
@auth_decorator
def delete_logo(uid):

    society = Society.query.filter_by(uid=uid).first()

    if not society:
        abort(404)

    crsid = auth_decorator.principal
    user = User.query.filter_by(crsid=crsid).first()

    if society not in user.societies:
        abort(403)

    delete_society_logo(uid)

    return redirect(url_for("admin.admin", uid=society.uid))

@bp.route("/<uid>/delete_bbb_logo")
@auth_decorator
def delete_bbb_logo(uid):

    society = Society.query.filter_by(uid=uid).first()

    if not society:
        abort(404)

    crsid = auth_decorator.principal
    user = User.query.filter_by(crsid=crsid).first()

    if society not in user.societies:
        abort(403)

    delete_society_bbb_logo(uid)

    return redirect(url_for("admin.admin", uid=society.uid))

@bp.route("/<uid>/delete", methods=("GET", "POST"))
@auth_decorator
def delete(uid):

    society = Society.query.filter_by(uid=uid).first()

    if not society:
        abort(404)

    crsid = auth_decorator.principal
    user = User.query.filter_by(crsid=crsid).first()

    if society not in user.societies:
        abort(403)

    if request.method == "POST":
        submitted_short_name = request.form.get("soc_short_name", "")

        errors = {}

        if society.short_name != submitted_short_name:
            errors["soc_short_name"] = "That is the wrong name."

        if errors:
            return render_template("admin/delete.html", page_title=f"Delete { society.name }", crsid=crsid, society=society, errors=errors)
        else:
            delete_society_logo(uid)

            db.session.delete(society)
            db.session.commit()

            return redirect(url_for("home.home"))

    else:
        return render_template("admin/delete.html", page_title=f"Delete { society.name }", crsid=crsid, society=society, errors={})
