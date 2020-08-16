from os import getenv
from urllib.parse import urlencode
from hashlib import sha1

import requests
import xmltodict

class BBB:

    # Create a new call.
    # Returns (True, "") if successful, otherwise (False, "[error_message]").
    def create(self, params):
        created = False
        message = ""
        response = self.request("create", params)

        if "returncode" not in response or "message" not in response:
            created = False
            message = "Error: Malformed response from server."
        else:
            if response["returncode"] != "SUCCESS":
                created = False
                message = response["message"]
            else:
                created = True

        return (created, message)


    # Join a call.
    # Returns (True, "[call_url]") if successful, otherwise
    # (False, "[error_message]").
    def join(self, params):
        joined = False
        message = ""
        call_url = ""
        response = self.request("join", params)

        if "returncode" not in response or "message" not in response:
            joined = False
            message = "Error: Malformed response from server."
        else:
            message = response["message"]
            if response["returncode"] != "SUCCESS":
                joined = False
            else:
                joined = True
                call_url = response["url"]

        if joined:
            return (joined, call_url)
        else:
            return (joined, message)


    # End a meeting.
    # Returns (True, "") if successful, otherwise (False, "[error_message]".
    def end(self, params):
        ended = False
        message = ""
        response = self.request("end", params)

        if "returncode" not in response or "message" not in response:
            ended = False
            message = "Error: Malformed response from server."
        else:
            if response["returncode"] != "SUCCESS":
                ended = False
                message = response["message"]
            else:
                ended = True

        return (ended, message)


    def request(self, call, params):
        url = self.build_url(call, params)
        res = requests.get(url, timeout=(0.5, 10))
        xml = xmltodict.parse(res.text)

        return xml["response"]


    def generate_checksum(self, call, query):
        hash_string = call + query + getenv("BIGBLUEBUTTON_SECRET")
        checksum = sha1(hash_string.encode()).hexdigest()

        return checksum


    def build_url(self, call, params):
        query = urlencode(params or {})
        query += "&checksum=" + self.generate_checksum(call, query)
        url = f"{getenv('BIGBLUEBUTTON_URL')}{call}?{query}"

        return url
