import re

from flask import Blueprint, render_template, request, flash, abort
from lightbluetent.models import db, Society

bp = Blueprint("society", __name__, url_prefix="/s")

email_re = re.compile(r"^\S+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+$")

@bp.route("/<uid>")
def welcome(uid):

    society = Society.query.filter_by(uid=uid).first()

    if not society:
        return abort(404)

    desc_paragraphs = {}
    # Split the description into paragraphs so it renders nicely.
    if society.description is not None:
        desc_paragraphs=society.description.split("\n")

    # Find the number of sessions registered on each day. We pass these to
    # render_template so we can detect the case where we have no registered sessions
    # by day.
    num_sessions_day_1_gen = (1 for session in society.sessions if session["day"] == "day_1")
    num_sessions_day_1 = sum(num_sessions_day_1_gen)
    num_sessions_day_2_gen = (1 for session in society.sessions if session["day"] == "day_2")
    num_sessions_day_2 = sum(num_sessions_day_2_gen)

    socials_1 = {}
    if society.social_1 is not None:

        socials_1["is_email"] = False
        socials_1["is_facebook"] = False
        socials_1["is_twitter"] = False
        socials_1["is_instagram"] = False
        socials_1["is_youtube"] = False

        if re.search(email_re, society.social_1):
            socials_1["is_email"] = True
        elif ("facebook." in society.social_1
                 or "fb.me" in society.social_1
                 or "fb.com" in society.social_1):
            socials_1["is_facebook"] = True
        elif ("twitter." in society.social_1
                 or "t.co" in society.social_1):
            socials_1["is_twitter"] = True
        elif "instagram." in society.social_1:
            socials_1["is_instagram"] = True
        elif ("youtube." in society.social_1
                 or "youtu.be" in society.social_1):
            socials_1["is_youtube"] = True

    socials_2 = {}
    if society.social_2 is not None:

        socials_2["is_email"] = False
        socials_2["is_facebook"] = False
        socials_2["is_twitter"] = False
        socials_2["is_instagram"] = False
        socials_2["is_youtube"] = False


        if re.search(email_re, society.social_2):
            socials_2["is_email"] = True
        elif ("facebook." in society.social_2
                 or "fb.me" in society.social_2
                 or "fb.com" in society.social_2):
            socials_2["is_facebook"] = True
        elif ("twitter." in society.social_2
                 or "t.co" in society.social_2):
            socials_2["is_twitter"] = True
        elif "instagram." in society.social_2:
            socials_2["is_instagram"] = True
        elif ("youtube." in society.social_2
                 or "youtu.be" in society.social_2):
            socials_2["is_youtube"] = True

    

    return render_template("society/welcome.html", page_title=f"{ society.name }",
                           society=society, desc_paragraphs=desc_paragraphs,
                           num_sessions_day_1=num_sessions_day_1,
                           num_sessions_day_2=num_sessions_day_2,
                           socials_1=socials_1, socials_2=socials_2)
