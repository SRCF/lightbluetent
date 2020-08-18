import uuid
import re

email_re = re.compile(r"^\S+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+$")

def gen_unique_string():
    return str(uuid.uuid4()).replace("-", "")

# Based on https://github.com/SRCF/control-panel/blob/master/control/webapp/utils.py#L249.
# Checks email is a valid email address and belongs to the currently authenticated crsid.
# Returns None if valid.
def validate_email(crsid, email):
    if isinstance(email, str):
        email = email.lower()

    print(f"{ email }")

    if not email:
        return "Enter your email address."
    elif not email_re.match(email):
        return "Enter a valid email address."
    elif email.endswith(("@cam.ac.uk", "@hermes.cam.ac.uk", "@o365.cam.ac.uk",
                         "@universityofcambridgecloud.onmicrosoft.com")):
        named = email.split("@")[0].split("+")[0]
        if named != crsid:
            return "You should use your own university email address."

    return None
