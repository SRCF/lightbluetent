import re
import os
import json

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
from lightbluetent.models import db, Group, User, Room, Authentication, Asset, Link
from lightbluetent.users import auth_decorator
from lightbluetent.api import Meeting
from lightbluetent.utils import (
    path_sanitise,
    gen_unique_string,
    gen_room_id,
    get_form_values,
    resize_image,
    match_link,
    match_link_name,
)
from flask_babel import _
from datetime import datetime
from PIL import Image, UnidentifiedImageError

bp = Blueprint("groups", __name__, url_prefix="/g")

email_re = re.compile(r"^\S+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+$")


@bp.route("/<group_id>")
def home(group_id):

    group = Group.query.filter_by(id=group_id).first()

    if not group:
        return abort(404)

    desc_paragraphs = {}
    # Split the description into paragraphs so it renders nicely.
    if group.description is not None:
        desc_paragraphs = group.description.split("\n")

    return render_template(
        "groups/home.html",
        page_title=f"{ group.name }",
        group=group,
        desc_paragraphs=desc_paragraphs,
        errors={},
    )


@auth_decorator
@bp.route("/<group_id>/rooms", methods=["GET"])
def rooms(group_id):
    crsid = auth_decorator.principal
    user = User.query.filter_by(crsid=crsid).first()
    group = Group.query.filter_by(id=group_id).first()

    if not group:
        abort(404)
    if group not in user.groups:
        abort(403)

    return render_template(
        "groups/rooms.html",
        group=group,
        user=user,
        page_parent=url_for("users.home"),
        page_title=f"{ group.name }'s rooms",
    )


@auth_decorator
@bp.route("/<group_id>/rooms/create", methods=["POST"])
def rooms_create(group_id):
    crsid = auth_decorator.principal
    user = User.query.filter_by(crsid=crsid).first()
    group = Group.query.filter_by(id=group_id).first()

    if not group:
        abort(404)
    if group not in user.groups:
        abort(403)

    errors = {}
    keys = ("room_name",)
    values = get_form_values(request, keys)

    if len(values["room_name"]) <= 1:
        errors["room_name"] = "That name is too short."

    if errors:
        flash("There were errors with the information you provided", "error")
        return render_template(
            "groups/rooms.html",
            group=group,
            user=user,
            page_parent=url_for("groups.home", group_id=group.id),
            page_title=f"{ group.name }'s rooms",
            errors=errors,
            **values,
        )
    else:
        id = gen_room_id(group.id)

        room = Room(
            id=id,
            name=values["room_name"],
            group_id=group.id,
            attendee_pw=gen_unique_string(),
            moderator_pw=gen_unique_string(),
            authentication=Authentication.PUBLIC,
            password=gen_unique_string()[0:6],
            whitelisted_users=group.owners,
        )

        db.session.add(room)
        user.groups.append(group)
        db.session.commit()
        current_app.logger.info(f"User { crsid } created room {values['room_name']}")
        flash("Created room successfully", "success")
        return redirect(url_for("groups.rooms", group_id=group.id))


@auth_decorator
@bp.route("/<group_id>/update/<update_type>", methods=["POST"])
def update(group_id, update_type):
    crsid = auth_decorator.principal
    user = User.query.filter_by(crsid=crsid).first()
    group = Group.query.filter_by(id=group_id).first()

    if group not in user.groups:
        abort(403)

    values = {}
    errors = {}

    if update_type == "group_settings":

        keys = ("name", "description")
        values = get_form_values(request, keys)

        if len(values["name"]) <= 1:
            errors["name"] = _("That name is too short.")

        if "logo" in request.files and request.files["logo"].filename != "":
            logo = request.files["logo"]

            try:
                assert logo.filename != ""
                logo_img = Image.open(logo)
            except (AssertionError, UnidentifiedImageError):
                errors["logo"] = "Invalid file."
            else:
                if not delete_logo(group.id):
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

        for link in group.links:
            url_field = request.form.get(f"{link.id}-url", "").strip()
            name_field = request.form.get(f"{link.id}-name", "").strip()
            # this means the link has been filled by the user
            if url_field != "":
                # validate name
                if len(name_field) > 40:
                    errors[f"{link.id}-name"] = "Choose a shorter link name"
                elif not match_link_name(name_field):
                    errors[f"{link.id}-name"] = "You must use valid characters"
                    current_app.logger.info(
                        f"Failed to validate link name: {name_field}"
                    )

                if not errors:
                    link.url = url_field
                    link.name = name_field
                    link.type = match_link(link.url)
                    if link in db.session.dirty:
                        current_app.logger.info(f"Updated link: {link}")

            else:
                # has the field been filled before?
                # ie, the user wants to delete it
                if link.url is not None:
                    db.session.delete(link)
                    group.preserve_display_order()
                    current_app.logger.info(f"Deleted link: {link}")

        if not errors:
            group.name = values["name"]
            group.description = (
                values["description"] if values["description"] != "" else None
            )

    elif update_type == "advanced_settings":

        values["new_owner_crsid"] = request.form.get("new_owner_crsid", "").strip()

        # Add a new owner
        if values["new_owner_crsid"]:
            current_app.logger.info(
                f"{ crsid } is adding new owner '{ values['new_owner_crsid'] }' to group '{ group.id }'..."
            )

            new_owner = User.query.filter_by(crsid=values["new_owner_crsid"]).first()
            if new_owner:
                group.owners.append(new_owner)
                current_app.logger.info(
                    f"New owner '{ new_owner.full_name }' added to group '{ group.id }'."
                )
            else:
                errors[
                    "new_owner_crsid"
                ] = "That user is not registered yet. Users must register before being added as owners."
    elif update_type == "links_order":
        links_order = request.get_json(force=True)
        for index, val in enumerate(links_order["order"]):
            Link.query.filter_by(group_id=group.id).filter_by(
                id=int(val)
            ).first().display_order = index
        db.session.commit()
        return json.dumps({"success": True}), 200, {"ContentType": "application/json"}
    else:
        current_app.logger.error(
            f"Attempted to update room page at incorrect endpoint: {update_type}"
        )

    if errors:
        flash(_("There were problems with the information you provided."))
        return render_template(
            "groups/manage.html",
            page_title=f"Settings for { group.name }",
            group=group,
            user=user,
            errors=errors,
            page_parent=url_for("users.home"),
            **values,
        )

    else:
        group.updated_at = datetime.now()
        db.session.commit()
        flash("Settings successfully saved.", "success")

        return redirect(url_for("groups.manage", group_id=group.id))


@bp.route("/<group_id>/manage", methods=["GET"])
@auth_decorator
def manage(group_id):
    group = Group.query.filter_by(id=group_id).first()

    if not group:
        return abort(404)

    crsid = auth_decorator.principal
    user = User.query.filter_by(crsid=crsid).first()

    # Check the user is registered with us, if not redirect to the user reg page
    if not user:
        return redirect(url_for("users.register"))

    if group not in user.groups:
        abort(403)

    values = {
        "name": group.name,
        "description": group.description,
    }

    return render_template(
        "groups/manage.html",
        group=group,
        user=user,
        page_parent=url_for("users.home"),
        page_title=f"Settings for { group.name }",
        errors={},
        **values,
    )


def delete_logo_variant(path):
    if not os.path.isfile(path):
        current_app.logger.info("no logo to delete")
        return False

    os.remove(path)
    current_app.logger.info(f"Deleted logo '{ path }'")


# Delete logo on disk for the group with given group_id
def delete_logo(group_id):
    images_dir = current_app.config["IMAGES_DIR"]
    if not os.path.isdir(images_dir):
        current_app.logger.info(f"'{ images_dir }':  no such directory.")
        return False

    group = Group.query.filter_by(id=group_id).first()
    if not group:
        return False

    if group.logo is None:
        return True

    current_app.logger.info(f"For id='{ group.id }': deleting logo...")
    for asset in Asset.query.filter_by(key=group.logo):
        old_logo = os.path.join(images_dir, asset.path)
        delete_logo_variant(old_logo)
        db.session.delete(asset)
    group.logo = None
    db.session.commit()
    return True


@bp.route("/<group_id>/delete_logo")
@auth_decorator
def delete_group_logo(group_id):
    group = Group.query.filter_by(id=group_id).first()

    if not group:
        abort(404)

    crsid = auth_decorator.principal
    user = User.query.filter_by(crsid=crsid).first()
    if group not in user.groups:
        abort(403)

    if not delete_logo(group.id):
        abort(500)
    else:
        return redirect(url_for("groups.manage", group_id=group.id))


@bp.route("/<group_id>/delete", methods=("GET", "POST"))
def delete(group_id):
    group = Group.query.filter_by(id=group_id).first()

    if not group:
        return abort(404)

    crsid = auth_decorator.principal
    user = User.query.filter_by(crsid=crsid).first()
    if group not in user.groups:
        abort(403)

    if request.method == "POST":
        submitted_id = request.form.get("group_id", "")

        errors = {}

        if group.id != submitted_id:
            errors["group_short_name"] = "That is the wrong name."

        if errors:
            return render_template(
                "groups/delete.html",
                page_title=f"Delete { group.name }",
                user=user,
                group=group,
                errors=errors,
            )
        else:
            for room in group.rooms:
                db.session.delete(room)

            db.session.commit()

            if not delete_logo(group.id):
                abort(500)

            db.session.delete(group)
            db.session.commit()

            current_app.logger.info(
                f"User { crsid } deleted group with id='{ group.id }'"
            )

            return redirect(url_for("users.home"))

    else:
        return render_template(
            "groups/delete.html",
            page_title=f"Delete { group.name }",
            user=user,
            group=group,
            errors={},
        )


# Check if a meeting is running. If it's not, create it. Redirect to the URL to
# join that meeting as a moderator with the provided name.
@bp.route("/<uid>/begin", methods=("GET", "POST"))
@auth_decorator
def begin_session(uid):

    group = Group.query.filter_by(uid=uid).first()

    if not group:
        return abort(404)

    crsid = auth_decorator.principal
    user = User.query.filter_by(crsid=crsid).first()
    if group not in user.groups:
        abort(403)

    meeting = Meeting(group)
    running = meeting.is_running()

    if running:
        page_title = "Join session"
    else:
        page_title = "Begin session"

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()

        errors = {}
        if len(full_name) <= 1:
            errors["full_name"] = "That name is too short."

        if errors:
            return render_template(
                "groups/begin_session.html",
                page_title=page_title,
                user=user,
                running=running,
                page_parent=url_for("users.home"),
                errors=errors,
            )

        if not running:
            join_url = url_for("groups.welcome", uid=group.uid, _external=True)
            moderator_only_message = _(
                "To invite others into this session, share your stall link: %(join_url)s",
                join_url=join_url,
            )
            success, message = meeting.create(moderator_only_message)
            current_app.logger.info(
                f"Moderator '{ full_name }' with CRSid '{ crsid }' created stall for '{ group.name }', bbb_id: '{ group.bbb_id }'"
            )

            if success:
                url = meeting.moderator_url(full_name)
                return redirect(url)
            else:
                # For some reason the meeting wasn't created.
                current_app.logger.error(f"Creation of stall failed: { message }")
                flash(
                    f"The session could not be created. Please contact an administrator at support@srcf.net and include the following: { message }"
                )

        else:
            url = meeting.moderator_url(full_name)
            current_app.logger.info(
                f"Moderator '{ full_name }' with CRSid '{ crsid }' joined stall for '{ group.name }', bbb_id: '{ group.bbb_id }'"
            )
            return redirect(url)

    return render_template(
        "groups/begin_session.html",
        page_title=page_title,
        user=user,
        running=running,
        page_parent=url_for("users.home"),
        errors={},
    )

