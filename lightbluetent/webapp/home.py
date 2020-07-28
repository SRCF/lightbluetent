from flask import Blueprint, render_template, redirect, url_for

from . import admin, utils, inspect_services


bp = Blueprint("home", __name__)


@bp.route('/')
def home():
    crsid = utils.auth.principal

    try:
        mem = utils.get_member(crsid)
    except KeyError:
        return redirect(url_for('signup.signup'))
    if not mem.user:
        return redirect(url_for('member.reactivate'))

    inspect_services.lookup_all(mem, fast=True)
    for soc in mem.societies:
        inspect_services.lookup_all(soc, fast=True)

    job_counts = None
    if utils.is_admin(mem):
        job_counts = [(key, count) for key, count in admin.job_counts()
                      if key in ("unapproved", "queued", "running") and count > 0]

    return render_template("home.html", member=mem, job_counts=job_counts)

@bp.route('/logout')
def logout():
    utils.auth.logout()
    return redirect(utils.DOMAIN_WEB, code=303)
