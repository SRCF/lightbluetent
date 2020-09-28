import os
import copy

from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    abort,
    redirect,
    url_for,
    current_app,
)
from lightbluetent.models import db, User, Group
from lightbluetent.users import auth_decorator
from lightbluetent.utils import gen_unique_string, match_social, get_social_by_id
from PIL import Image
from flask_babel import _
from datetime import time, datetime
from sqlalchemy.orm.attributes import flag_modified

bp = Blueprint("rooms", __name__, url_prefix="/r")


def remove_logo(path):

    images_dir = current_app.config["IMAGES_DIR"]

    if not os.path.isdir(images_dir):
        current_app.logger.info(f"'{ images_dir }':  no such directory.")
        abort(500)

    if not os.path.isfile(path):
        current_app.logger.info(f"no logo to delete")
        return

    os.remove(path)
    current_app.logger.info(f"Deleted logo '{ path }'")


# Delete logo on disk for the group with given uid
def delete_group_logo(uid):

    images_dir = current_app.config["IMAGES_DIR"]

    group = Group.query.filter_by(uid=uid).first()

    if group.logo == current_app.config["DEFAULT_LOGO"]:
        return
    else:
        current_app.logger.info(f"For uid='{ group.uid }': deleting logo...")
        old_logo = os.path.join(images_dir, group.logo)
        remove_logo(old_logo)
        group.logo = current_app.config["DEFAULT_LOGO"]
        db.session.commit()
        return


# Delete logo on disk for the group with given uid
def delete_group_bbb_logo(uid):

    group = Group.query.filter_by(uid=uid).first()

    images_dir = current_app.config["IMAGES_DIR"]

    if group.bbb_logo == current_app.config["DEFAULT_BBB_LOGO"]:
        return
    else:
        current_app.logger.info(f"For uid='{ group.uid }': deleting bbb_logo")
        old_logo = os.path.join(images_dir, group.bbb_logo)
        remove_logo(old_logo)
        group.bbb_logo = current_app.config["DEFAULT_BBB_LOGO"]
        db.session.commit()
        return


# Delete one of the saved sessions in the database, identified by its ID.
# Returns if that session_id doesn't exist.
def delete_group_session(uid, session_id):
    group = Group.query.filter_by(uid=uid).first()
    sessions = copy.deepcopy(group.sessions)
    session_to_delete = next(
        (session for session in sessions if session["id"] == session_id), None
    )

    if session_to_delete is None:
        return
    else:
        current_app.logger.info(
            f"For uid='{ group.uid }': deleting session [ day: { session_to_delete['day'] }, start: { session_to_delete['start'] }, end: { session_to_delete['end'] } ]"
        )
        sessions.remove(session_to_delete)
        group.sessions = sessions
        db.session.commit()
        return


@bp.route("/<uid>", methods=("GET", "POST"))
@auth_decorator
def manage(uid):

    has_directory_page = current_app.config["HAS_DIRECTORY_PAGE"]

    group = Group.query.filter_by(uid=uid).first()

    if not group:
        abort(404)

    crsid = auth_decorator.principal
    user = User.query.filter_by(crsid=crsid).first()

    if group not in user.societies:
        abort(403)

    sessions_data = {"days": current_app.config["NUMBER_OF_DAYS"]}

    if request.method == "POST":

        is_new_owner = False
        is_new_session = False

        # Input validation from https://github.com/SRCF/control-panel/blob/master/control/webapp/signup.py#L37

        values = {}

        for key in (
            "group_name",
            "website",
            "description",
            "short_description",
            "welcome_text",
            "logo",
            "banner_text",
            "banner_color",
            "new_owner_crsid",
            "new_session_day",
            "new_session_start",
            "new_session_end",
        ):
            values[key] = request.form.get(key, "").strip()

        for key in ("mute_on_start", "disable_private_chat"):
            values[key] = bool(request.form.get(key, False))

        errors = {}

        if len(values["group_name"]) <= 1:
            errors["group_name"] = _("That name is too short.")

        if len(values["short_description"]) > 200:
            errors["short_description"] = _("This description is too long.")

        if "logo" in request.files:
            logo = request.files["logo"]
            bbb_logo = request.files["bbb_logo"]

            logo_filename, logo_extension = os.path.splitext(logo.filename)
            bbb_logo_filename, bbb_logo_extension = os.path.splitext(bbb_logo.filename)

            images_dir = current_app.config["IMAGES_DIR"]

            if logo and logo_filename != "":
                if logo_extension in current_app.config["LOGO_ALLOWED_EXTENSIONS"]:

                    # Delete the old logo if it's not the default
                    delete_group_logo(uid)

                    static_filename = (
                        group.uid + "_" + gen_unique_string() + logo_extension
                    )
                    path = os.path.join(images_dir, static_filename)

                    current_app.logger.info(
                        f"For user { crsid }, group uid='{ group.uid }': changing logo..."
                    )
                    if not os.path.isdir(images_dir):
                        current_app.logger.error(
                            f"'{ images_dir }':  no such directory."
                        )
                        abort(500)

                    maxwidth, maxheight = current_app.config["MAX_LOGO_SIZE"]
                    logo_img = Image.open(logo)
                    ratio = min(maxwidth / logo_img.width, maxheight / logo_img.height)
                    # possible optimization with reduce here?
                    logo_resized = logo_img.resize(
                        (round(logo_img.width * ratio), round(logo_img.height * ratio))
                    )
                    logo_resized.save(path)

                    current_app.logger.info(
                        f"For uid='{ group.uid }': saved new logo '{ path }'"
                    )

                    group.logo = static_filename
                    db.session.commit()
                    current_app.logger.info(f"For uid='{ group.uid }': updated logo.")
                else:
                    errors["logo"] = "Invalid file."

            if bbb_logo and bbb_logo_filename != "":
                if bbb_logo_extension in current_app.config["LOGO_ALLOWED_EXTENSIONS"]:

                    # Delete the old logo if it's not the default
                    delete_group_bbb_logo(uid)

                    static_filename = (
                        group.uid + "_bbb_" + gen_unique_string() + bbb_logo_extension
                    )
                    path = os.path.join(images_dir, static_filename)

                    current_app.logger.info(
                        f"For user { crsid }, group uid='{ group.uid }': changing bbb_logo..."
                    )
                    if not os.path.isdir(images_dir):
                        current_app.logger.error(
                            f"'{ images_dir }':  no such directory."
                        )
                        abort(500)

                    bbb_logo_img = Image.open(bbb_logo)
                    bbb_logo_resized = bbb_logo_img.resize((100, 30))
                    bbb_logo_resized.save(path)

                    current_app.logger.info(
                        f"For uid='{ group.uid }': saved new bbb_logo to '{ path }'"
                    )

                    group.bbb_logo = static_filename
                    db.session.commit()
                    current_app.logger.info(
                        f"For uid='{ group.uid }': updated bbb_logo."
                    )
                else:
                    errors["bbb_logo"] = "Invalid file."

        # TODO: tweak these values when their ideal maximum lengths become apparent
        if len(values["welcome_text"]) > 100:
            errors["welcome_text"] = "Welcome text is too long."
        if len(values["banner_text"]) > 100:
            errors["banner_text"] = "Banner text is too long."

        # Adding a new owner
        if values["new_owner_crsid"] != "":

            current_app.logger.info(
                f"For uid='{ group.uid }': { crsid } is adding new owner { values['new_owner_crsid'] }..."
            )
            new_owner = User.query.filter_by(crsid=values["new_owner_crsid"]).first()
            if not new_owner:
                errors[
                    "new_owner_crsid"
                ] = "That user is not registered yet. Users must register before being added as administrators."
            is_new_owner = True

        # Add a new session
        if values["new_session_start"] and values["new_session_end"]:

            start_time = [int(nstr) for nstr in values["new_session_start"].split(":")]
            end_time = [int(nstr) for nstr in values["new_session_end"].split(":")]

            # Check that start is before end
            t1 = time(hour=start_time[0], minute=start_time[1])
            t2 = time(hour=end_time[0], minute=end_time[1])

            if t1 > t2:
                errors[
                    "new_session_start"
                ] = "Unfortunately, time travel is not possible."

            is_new_session = True

        elif values["new_session_start"]:
            errors["new_session_end"] = "No end time specified."
        elif values["new_session_end"]:
            errors["new_session_start"] = "No start time specified."

        if errors:
            flash("There are errors with the information you provided.")
            return render_template(
                "rooms/manage.html",
                page_title=f"Stall administration for { group.name }",
                group=group,
                user=user,
                errors=errors,
                sessions_data=sessions_data,
                page_parent=url_for("users.home"),
                has_directory_page=has_directory_page,
                **values,
            )
        else:
            group.name = values["group_name"]
            group.website = values["website"] if values["website"] != "" else None

            # fetch all social fields from values, as we generate the uid in jinja
            social_forms = {k: v for (k, v) in request.form.items() if ("social-" in k)}
            for id, value in social_forms.items():
                index, found_social = get_social_by_id(id, group.socials)
                # do we have this social already?
                if found_social:
                    if found_social["url"] != value:
                        if value == "":
                            del group.socials[index]
                        else:
                            found_social["url"] = value
                            found_social["type"] = match_social(value)
                    flag_modified(group, "socials")
                else:
                    # create a new social field
                    # and check if its empty
                    if value:
                        social_type = match_social(value)
                        social_data = {"id": id, "url": value, "type": social_type}
                        group.socials.append(social_data)
                        flag_modified(group, "socials")

            group.description = values["description"] if values["description"] != "" else None
            group.short_description = values["short_description"] if values["short_description"] != "" else None
            group.welcome_text = values["welcome_text"] if values["welcome_text"] != "" else None
            group.banner_text = values["banner_text"] if values["banner_text"] != "" else None
            group.banner_color = values["banner_color"]
            group.mute_on_start = values["mute_on_start"]
            group.disable_private_chat = values["disable_private_chat"]

            if is_new_owner:
                group.owners.append(new_owner)

            if is_new_session:
                group.sessions.append(
                    {
                        "id": gen_unique_string(),
                        "day": values["new_session_day"],
                        "start": values["new_session_start"],
                        "end": values["new_session_end"],
                    }
                )
                # we need this to ensure that sqlalchemy updates the val
                flag_modified(group, "sessions")

            group.updated_at = datetime.now()
            db.session.commit()

            if is_new_owner:
                current_app.logger.info(
                    f"For uid='{ group.uid }': added new owner { new_owner }."
                )

            if is_new_session:
                current_app.logger.info(
                    f"For uid='{ group.uid }': { crsid } added new session [ day: { values['new_session_day'] }, start: { values['new_session_start'] }, end: { values['new_session_end'] } ]"
                )

            flash("Settings saved.")

            return redirect(url_for("rooms.manage", uid=group.uid))

    else:
        # defaults
        values = {
            "group_name": group.name,
            "website": group.website,
            "description": group.description,
            "short_description": group.short_description,
            "welcome_text": group.welcome_text,
            "banner_text": group.banner_text,
            "banner_color": group.banner_color,
            "logo": group.logo,
            "mute_on_start": group.mute_on_start,
            "disable_private_chat": group.disable_private_chat,
        }

    return render_template(
        "rooms/manage.html",
        page_title=f"Stall administration for { group.name }",
        group=group,
        user=user,
        errors={},
        sessions_data=sessions_data,
        page_parent=url_for("users.home"),
        has_directory_page=has_directory_page,
        **values,
    )


@bp.route("/<uid>/reset_banner")
@auth_decorator
def reset_banner(uid):
    group = Group.query.filter_by(uid=uid).first()

    if not group:
        abort(404)

    crsid = auth_decorator.principal
    user = User.query.filter_by(crsid=crsid).first()

    if group not in user.societies:
        abort(403)

    if group.banner_text != None:
        group.banner_text = None

    if group.banner_color != "#e8e8e8":
        group.banner_color = "#e8e8e8"

    db.session.commit()

    return redirect(url_for("rooms.manage", uid=group.uid))


@bp.route("/<uid>/delete_logo")
@auth_decorator
def delete_logo(uid):

    group = Group.query.filter_by(uid=uid).first()

    if not group:
        abort(404)

    crsid = auth_decorator.principal
    user = User.query.filter_by(crsid=crsid).first()

    if group not in user.societies:
        abort(403)

    current_app.logger.info(
        f"User { crsid } deleting logo { group.logo } for uid '{ group.uid }'..."
    )

    delete_group_logo(uid)

    return redirect(url_for("rooms.manage", uid=group.uid))


@bp.route("/<uid>/delete_bbb_logo")
@auth_decorator
def delete_bbb_logo(uid):

    group = Group.query.filter_by(uid=uid).first()

    if not group:
        abort(404)

    crsid = auth_decorator.principal
    user = User.query.filter_by(crsid=crsid).first()

    if group not in user.societies:
        abort(403)

    current_app.logger.info(
        f"User { crsid } deleting bbb_logo { group.bbb_logo } for uid '{ group.uid }'..."
    )

    delete_group_bbb_logo(uid)

    return redirect(url_for("rooms.manage", uid=group.uid))


@bp.route("/<uid>/delete_session/<session_id>")
@auth_decorator
def delete_session(uid, session_id):

    group = Group.query.filter_by(uid=uid).first()

    if not group:
        abort(404)

    crsid = auth_decorator.principal

    current_app.logger.info(
        f"User { crsid } deleting session { session_id } for uid '{ group.uid }'..."
    )

    user = User.query.filter_by(crsid=crsid).first()

    if group not in user.societies:
        abort(403)

    delete_group_session(uid, session_id)

    return redirect(url_for("rooms.manage", uid=group.uid))


@bp.route("/<uid>/delete", methods=("GET", "POST"))
@auth_decorator
def delete(uid):

    group = Group.query.filter_by(uid=uid).first()

    if not group:
        abort(404)

    crsid = auth_decorator.principal
    user = User.query.filter_by(crsid=crsid).first()

    if group not in user.societies:
        abort(403)

    if request.method == "POST":
        submitted_short_name = request.form.get("group_short_name", "")

        errors = {}

        if group.short_name != submitted_short_name:
            errors["group_short_name"] = "That is the wrong name."

        if errors:
            return render_template(
                "rooms/delete.html",
                page_title=f"Delete { group.name }",
                user=user,
                group=group,
                errors=errors,
            )
        else:
            delete_group_logo(uid)

            db.session.delete(group)
            db.session.commit()

            current_app.logger.info(
                f"User { crsid } deleted group with uid='{ group.uid }'"
            )

            return redirect(url_for("users.home"))

    else:
        return render_template(
            "rooms/delete.html",
            page_title=f"Delete { group.name }",
            crsid=crsid,
            group=group,
            errors={},
        )

