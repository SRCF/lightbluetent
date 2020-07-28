import sys
import traceback
from urllib.parse import urlparse

import flask
import jinja2
import ucam_webauth
import ucam_webauth.rsa
import ucam_webauth.flask_glue
import ucam_webauth.raven.flask_glue
from werkzeug.exceptions import HTTPException


raven = ucam_webauth.raven.flask_glue.AuthDecorator(desc="SRCF Freshers' Fair",
                                                    require_ptags=None)

def parse_domain_name(domain):
    parsed = urlparse(domain.lower())
    domain = parsed.netloc or parsed.path.split("/", 1)[0]
    while domain.startswith("www."):
        domain = domain[4:]
    if all(ord(char) < 128 for char in domain):
        return domain
    else:
        # convert to punycode
        return domain.encode("idna").decode("ascii")


# Template helpers
def sif(variable, val):
    """"string if": `val` if `variable` is defined and truthy, else ''"""
    if not jinja2.is_undefined(variable) and variable:
        return val
    else:
        return ""


def generic_error_handler(error):
    if isinstance(error, HTTPException):
        return flask.render_template("error.html", error=error), error.code
    else:
        tb = traceback.format_exception(*sys.exc_info())
        return flask.render_template("error_tb.html", error=error, tb=tb), 500


def validate_member_email(crsid, email):
    """
    Validate an email address destined to be a member's registered address.

    Does sane checks like preventing SRCF addresses (which defeat the point of
    the registered address), and preventing email addresses that we know don't
    belong to the member (e.g. @cam.ac.uk addresses with a different CRSid).

    Returns None if valid, or a user-friendly error message otherwise.
    """
    if isinstance(email, str):
        email = email.lower()

    if not email:
        return "Please enter your email address."
    elif not email_re.match(email):
        return "That address doesn't look valid."
    elif email.endswith(("@srcf.net", "@srcf.ucam.org", "@hades.srcf.net")):
        return "This should be an external email address."
    elif email.endswith(("@cam.ac.uk", "@hermes.cam.ac.uk", "@o365.cam.ac.uk",
                         "@universityofcambridgecloud.onmicrosoft.com")):
        named = email.split("@")[0].split("+")[0]
        if named != crsid:
            return "You should use only your own University email address."

    return None
