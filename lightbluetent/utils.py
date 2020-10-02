import uuid
import re
import sys
import requests
from jinja2 import is_undefined
from flask import render_template
import traceback
from lightbluetent.models import db
import re
import unicodedata
import hashlib

email_re = re.compile(r"^\S+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+$")
time_re = re.compile(r"\d{2}:\d{2}")


def table_exists(name):
    ret = db.engine.dialect.has_table(db.engine, name)
    return ret


def gen_unique_string():
    return str(uuid.uuid4()).replace("-", "")


def path_sanitise(unsafe, maintain_uniqueness=4, forbidden=r'[^a-zA-Z0-9_-]'):
    """generate a string safe for use in filenames etc from unsafe;
    if maintain_uniqueness is not False, then we append a hashed version
    of unsafe to minimise risk of collision between, e.g.,
      cafe
    and
      café
    maintain_uniqueness should be the number of bytes of entropy to retain
    """
    normed = unicodedata.normalize('NFD', unsafe)
    safe = re.sub(forbidden, '_', normed)
    if maintain_uniqueness is not False:
        hash_ = hashlib.sha256(unsafe.encode()).hexdigest()
        safe += '_' + hash_[:int(2*maintain_uniqueness)]
    return safe


# Based on https://github.com/SRCF/control-panel/blob/master/control/webapp/utils.py#L249.
# Checks email is a valid email address and belongs to the currently authenticated crsid.
# Returns None if valid.
def validate_email(crsid, email):
    if isinstance(email, str):
        email = email.lower()

    if not email:
        return "Enter your email address."
    elif not email_re.match(email):
        return "Enter a valid email address."
    elif email.endswith(
        (
            "@cam.ac.uk",
            "@hermes.cam.ac.uk",
            "@o365.cam.ac.uk",
            "@universityofcambridgecloud.onmicrosoft.com",
        )
    ):
        named = email.split("@")[0].split("+")[0]
        if named != crsid:
            return "You should use your own university email address."

    return None


def sif(variable):
    """"string if": `variable` is defined and truthy, else ''"""
    if not is_undefined(variable) and variable:
        return variable
    else:
        return ""


# write an enum for this?
def match_social(value):
    if re.search(email_re, value):
        return "email"
    elif any(match in value for match in ["facebook.", "fb.me", "fb.com"]):
        return "facebook"
    elif any(match in value for match in ["twitter.", "t.co", "fb.com"]):
        return "twitter"
    elif "instagram." in value:
        return "instagram"
    elif any(match in value for match in ["youtube.", "youtu.be"]):
        return "youtube"
    else:
        return "link"


def get_social_by_id(id, socials):
    if socials:
        for index, social in enumerate(socials):
            if social["id"] == id:
                return (index, social)
    return (False, False)


def match_time(time):
    return time_re.match(time)


# from django humanize
def ordinal(value):
    """
    Converts an integer to its ordinal as a string. 1 is '1st', 2 is '2nd',
    3 is '3rd', etc. Works for any integer.
    """
    try:
        value = int(value)
    except (TypeError, ValueError):
        return value
    suffixes = ("th", "st", "nd", "rd", "th", "th", "th", "th", "th", "th")
    if value % 100 in (11, 12, 13):  # special case
        return "%d%s" % (value, suffixes[0])
    return "%d%s" % (value, suffixes[value % 10])


def page_not_found(e):
    return render_template("error.html", error=e), 404


def server_error(e):
    tb = traceback.format_exception(*sys.exc_info())
    return render_template("error.html", error=e, tb=tb), 500


def fetch_lookup_data(crsid):
    url = f"https://www.lookup.cam.ac.uk/api/v1/person/crsid/{crsid}"
    res = requests.get(
        url,
        params={"fetch": "email,departingEmail", "format": "json"},
        timeout=(0.5, 10),
    )
    if res.status_code == 200:
        # request successful
        response = res.json()["result"]["person"]

        email = ""
        if len(response["attributes"]) > 0:
            email = response["attributes"][0]["value"]
        else:
            email = f"{crsid}@cam.ac.uk"

        return {
            "name": response["visibleName"],
            "email": email
        }
    elif res.status_code == 401:
        # not authorized, we're outside of the cudn
        return {
            "email": "mug99@cam.ac.uk",
            "name": "Testing Software"
        }
    else:
        # something bad happened, don't prefill any fields
        return None
