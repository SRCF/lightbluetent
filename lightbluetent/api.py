from os import getenv
from urllib.parse import urlencode
from hashlib import sha1
from flask import current_app, url_for
from lightbluetent.models import Asset

import requests
import xmltodict
import os

# Represents a meeting for a group.
# Usage:
# meeting = Meeting.query.filter_by(id=id).first()
# meeting = Meeting(room)
# created, msg = meeting.create("Moderator-only message")
# if not created:
#     # do something with msg, e.g. redirect to error page
# if meeting.is_running:
#     redirect(meeting.moderator_url(name))
class Meeting:

    def __init__(self, room):

        self.id = room.id
        self.room_name = room.name
        self.welcome_text = room.welcome_text
        self.banner_text = room.banner_text
        self.banner_color = room.banner_color
        self.mute_on_start = room.mute_on_start
        self.disable_private_chat = room.disable_private_chat
        self.attendee_pw = room.attendee_pw
        self.moderator_pw = room.moderator_pw

        self.alias = room.alias


    def create(self, moderator_only_message=""):
        params = {}
        params["name"] = self.room_name
        params["meetingID"] = self.id
        params["attendeePW"] = self.attendee_pw
        params["moderatorPW"] = self.moderator_pw
        params["welcome"] = self.welcome_text if self.welcome_text != None else ""
        params["moderatorOnlyMessage"] = moderator_only_message
        params["bannerText"] = self.banner_text if self.banner_text != None else ""
        params["bannerColor"] = self.banner_color
        params["muteOnStart"] = "true" if self.mute_on_start else "false"
        params["lockSettingsDisablePrivateChat"] = "true" if self.disable_private_chat else "false"

        if self.alias:
            params["logoutURL"] = url_for("room_aliases.home", room_alias=self.alias, _external=True)
        else:
            params["logoutURL"] = url_for("room_aliases.home", room_id=self.id, _external=True)

        response, error = self.request("create", params)

        if response is None:
            return (False, error)

        if response["returncode"] != "SUCCESS":
            current_app.logger.error(f"Error creating meeting: { response['message'] }")
            return (False, f"Error creating meeting: { response['message'] }")

        return (True, "")


    def moderator_url(self, full_name):
        params = {}
        params["fullName"] = full_name
        params["meetingID"] = self.id
        params["password"] = self.moderator_pw
        params["redirect"] = "true"

        '''
        if self.logo is not None:
            logo_subpath = Asset.query.filter_by(key=self.logo).first().path
            logo_path = os.path.join(current_app.config["IMAGES_DIR_FROM_STATIC"], logo_subpath)
            params["logo"] = url_for("static", filename=logo_path, _external=True)
            params["userdata-bbb_display_branding_area"] = "true"

            # Custom styling to make the bbb_logo look better
            params["userdata-bbb_custom_style"] = ".branding--Z1T4eH0>img{display:block;margin-right:auto;margin-left:auto;}.separator--Z3YSEe{margin-top:0;}.branding--Z1T4eH0 {padding:var(--sm-padding-x);}"'''

        return self.build_url("join", params)


    def attendee_url(self, full_name):
        params = {}
        params["fullName"] = full_name
        params["meetingID"] = self.id
        params["password"] = self.attendee_pw
        params["redirect"] = "true"

        '''
        if self.logo is not None:
            logo_subpath = Asset.query.filter_by(key=self.logo).first().path
            logo_path = os.path.join(current_app.config["IMAGES_DIR_FROM_STATIC"], logo_subpath)
            params["logo"] = url_for("static", filename=logo_path, _external=True)
            params["userdata-bbb_display_branding_area"] = "true"

            # Custom styling to make the bbb_logo look better
            params["userdata-bbb_custom_style"] = ".branding--Z1T4eH0>img{display:block;margin-right:auto;margin-left:auto;}.separator--Z3YSEe{margin-top:0;}.branding--Z1T4eH0 {padding:var(--sm-padding-x);}"'''

        return self.build_url("join", params)

    def is_running(self):
        params = {}
        params["meetingID"] = self.id

        response, error = self.request("isMeetingRunning", params)

        if response is None:
            return False

        if response["returncode"] != "SUCCESS":
            current_app.logger.error(f"Error checking meeting status: { response.message }")
            return False

        return True if response["running"] == "true" else False


    # Private API #

    # Make a request. Returns None, error_msg if
    #   a) the request timed out, or
    #   b) an error response was received, or
    #   c) the reponse was malformed, or
    #   d) the reponse was not a valid BBB response (i.e. missing returncode key).
    def request(self, call, params):
        url = self.build_url(call, params)

        try:
            res = requests.get(url, timeout=(0.5, 10))

        except requests.exceptions.ReadTimeout:
            current_app.logger.error(f"Timeout timed out! Requests.exceptions.ReadTimeout when making API call { call }")
            return (None, f"Timeout timed out! Requests.exceptions.ReadTimeout when making API call { call }")

        if res.status_code != requests.codes.ok:
            current_app.logger.error(f"Error { res.status_code } from server: { res.text }")
            return (None, f"Error { res.status_code } from server: { res.text }")

        xml = xmltodict.parse(res.text)

        if "response" not in xml:
            current_app.logger.error(f"Malformed response from server: { xml }")
            return (None, f"Malformed response from server: { xml }")
        if "returncode" not in xml["response"]:
            current_app.logger.error(f"Malformed response from server: { xml }: no returncode")
            return (None, f"Malformed response from server: { xml }: no returncode")
        else:
            return (xml["response"], "")


    def generate_checksum(self, call, query):
        hash_string = call + query + getenv("BIGBLUEBUTTON_SECRET")
        checksum = sha1(hash_string.encode()).hexdigest()

        return checksum


    def build_url(self, call, params):
        query = urlencode(params or {})
        query += "&checksum=" + self.generate_checksum(call, query)
        url = f"{getenv('BIGBLUEBUTTON_URL')}{call}?{query}"

        return url
