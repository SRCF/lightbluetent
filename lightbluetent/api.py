from os import getenv
from urllib.parse import urlencode
from hashlib import sha1

import requests
import xmltodict


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
    query += "&checksum=" + self.request_checksum(
        call, query, getenv("BIGBLUEBUTTON_SECRET")
    )
    url = f"{getenv('BIGBLUEBUTTON_URL')}{call}?{query}"

    return url
