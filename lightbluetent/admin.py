from flask import Blueprint, render_template, request, flash, abort, redirect, url_for
from lightbluetent.models import db, User, Society
from lightbluetent.home import auth_decorator

bp = Blueprint("admin", __name__, url_prefix="/admin")

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

        print(values["mute_on_start"])
        print(values["disable_private_chat"])
        print(values["description"])

        errors = {}

        if len(values["soc_name"]) <= 1:
            errors["soc_name"] = "Society name is too short."

       # if "logo" in request.files:
        #    logo = request.files["logo"]
#
 #           if logo.filename == "":
  #              errors["logo"] = "Invalid file name."

        # TODO: validate and process the logo

        # TODO: tweak these values when their ideal maximum lengths become apparent
        if len(values["welcome_text"]) > 100:
            errors["welcome_text"] = "Welcome text is too long."
        if len(values["banner_text"]) > 100:
            errors["banner_text"] = "Banner text is too long."

        # Adding a new admin
        if values["new_admin_crsid"] is not "":

            new_admin = User.query.filter_by(crsid=values["new_admin_crsid"]).first()
            if not new_admin:
                errors["new_admin_crsid"] = "That user is not registered yet. Users must register before being added as administrators."
            else:
                society.admins.append(new_admin)

        if errors:
            return render_template("admin/admin.html", page_title=f"Settings for { society.name }", society=society, crsid=crsid, errors=errors, **values)
        else:
            society.name = values["soc_name"]
            society.website = values["website"]
            society.description = values["description"]
            society.welcome_text = values["welcome_text"]
            society.logo = values["logo"]
            society.banner_text = values["banner_text"]
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

    print(values["website"])

    return render_template("admin/admin.html", page_title=f"Settings for { society.name }", society=society, crsid=crsid, errors={}, **values)

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

        print(society.short_name)
        print(submitted_short_name)

        if society.short_name != submitted_short_name:
            errors["soc_short_name"] = "That is the wrong name."

        if errors:
            return render_template("admin/delete.html", page_title=f"Delete { society.name }", crsid=crsid, society=society, errors=errors)
        else:
            db.session.delete(society)
            db.session.commit()

            return redirect(url_for("home.home"))

    else:
        return render_template("admin/delete.html", page_title=f"Delete { society.name }", crsid=crsid, society=society, errors={})


# TODO: delete society?
# TODO: add more admins 
