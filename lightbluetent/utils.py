import os
import uuid
import re
import sys
import requests
from jinja2 import is_undefined, Markup
from flask import render_template, url_for, current_app
import traceback
from lightbluetent.models import db, Asset
import re
import unicodedata
import hashlib
from PIL import Image
import math

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

def resize_image(image, max_dimensions, *, preserve_aspect=True, grow=False, fill_canvas=(0,0,0,0), fill_composite=True, attachment=(0.5,0.5), hidpi=[1,2]):
    """
    Resize an image using pillow 'smartly'
      max_dimensions:
        a (w,h) tuple specifying the maximum _logical_ dimensions of the 
        resulting image
      preserve_aspect:
        a bool specifying whether or not to preserve the aspect ratio
      grow:
        a bool specifying whether to allow a dimension to be stretched
      fill_canvas:
        either False in which case the resulting image size may be smaller
        than max_dimensions, or a valid pillow colour in which case the canvas
        will be enlarged to match max_dimensions whilst still preserving the
        aspect ratio if desired; the specified colour is used to fill the
        background, and by default is transparent
      fill_composite:
        if True, then transparent areas of the original image will also be
        filled by the fill colour
      attachment:
        if the canvas is enlarged, then attachment specifies where the image
        is placed; (0,0) means top-left, (0.5,0.5) means centered, etc
      hidpi:
        a list of hidpi resolutions to output
    """

    if not isinstance(image, Image.Image):
        image = Image.open(image)
    image = image.convert("RGBA")

    orig_width, orig_height = image.size
    max_lwidth, max_lheight = max_dimensions

    ratio_x = max_lwidth / orig_width
    ratio_y = max_lheight / orig_height
    if not grow:
        ratio_x = min(1, ratio_x)
        ratio_y = min(1, ratio_y)

    new_lwidth = round(ratio_x * orig_width)
    new_lheight = round(ratio_y * orig_height)

    if preserve_aspect:
        if ratio_x < ratio_y:
            new_lwidth = max_lwidth
        elif ratio_y < ratio_x:
            new_lheight = max_lheight
        else:
            new_lwidth = max_lwidth
            new_lheight = max_lheight
        ratio_x = ratio_y = min(ratio_x, ratio_y)

    if fill_canvas is not False:
        canv_width = math.ceil(max_lwidth / ratio_x)
        canv_height = math.ceil(max_lheight / ratio_y)
        att_rx, att_ry = attachment
        att_x = math.floor(att_rx * (canv_width - orig_width))
        att_y = math.floor(att_ry * (canv_height - orig_height))

        canvas_size = canv_width, canv_height
        canvas = Image.new("RGBA", canvas_size, fill_canvas)
        if fill_composite:
            canvas2 = Image.new("RGBA", canvas_size, (0,0,0,0))
            canvas2.paste(image, (att_x, att_y))
            image = Image.alpha_composite(canvas, canvas2)
        else:
            canvas.paste(image, (att_x, att_y))
            image = canvas

        orig_width, orig_height = image.size
        new_lwidth = max_lwidth
        new_lheight = max_lheight

    for px_density in hidpi:
        out_width = new_lwidth*px_density
        out_height = new_lheight*px_density
        if not grow:
            print((out_width, out_height), (orig_width, orig_height))
        if not grow and (out_width > orig_width or out_height > orig_height):
            continue
        yield px_density, image.resize((out_width, out_height))


class responsive_image:
    resp_re = re.compile(r'^@([0-9]+(.[0-9]+)?)x$')
    def __init__(self, key):
        main_res = 0
        main = None
        variants = {}
        for variant in Asset.query.filter_by(key=key):
            path = os.path.join(current_app.config["IMAGES_DIR_FROM_STATIC"], variant.path)
            path = url_for('static', filename=path)
            if variant.variant is None:
                main = path
                main_res = float('inf')
            elif (m := resp_re.match(variant.variant)) is not None:
                v = m.group(1)
                vf = float(v)
                if (vf := float(v)) > main_res:
                    main_res = vf
                    main = path
                variants[v] = path
            else:
                # should we warn/throw an error?
                pass
        self.main = main
        self.variants = variants

    def img_attr(self, raw=False):
        srcset = []
        for res, url in self.variants.items():
            srcset.append(f"{url} {res}x")
        srcset = ", ".join(srcset)
        if srcset:
            srcset = f" srcset=\"{srcset}\""
        attrs = f"src=\"{self.main}\"" + srcset
        if not raw:
            attrs = Markup(attrs)
        return attrs

    def css(self, prop='background-image'):
        # not too widely supported, would be better to provide
        # tooling for generating appropriate media queries

        srcset = []
        for res, url in self.variants.items():
            srcset.append(f"url({url}) {res}x")
        srcset = ", ".join(srcset)
        props = f"{prop}:url({self.main});"
        if srcset:
            props += f"{prop}:-webkit-image-set({srcset});"
            props += f"{prop}:image-set({srcset});"
        if not raw:
            props = Markup(props)
        return props

@current_app.template_filter('responsive_image.img')
def responsive_image_filter_img(key):
    return responsive_image(key).img_attr()
@current_app.template_filter('responsive_image.css')
def responsive_image_filter_css(key, prop='background-image'):
    return responsive_image(key).css(prop)
@current_app.template_filter('responsive_image.main')
def responsive_image_filter_main(key):
    return responsive_image(key).main

