import uuid
import requests


def gen_unique_string():
    return str(uuid.uuid4()).replace("-", "")


def fetch_lookup_data(crsid):
    url = f"https://www.lookup.cam.ac.uk/api/v1/person/crsid/{crsid}"
    res = requests.get(url, params={"fetch": "email,departingEmail", "format": "json"}, timeout=(0.5, 10))
    if res.status_code == 200:
        # request successful
        return res.json()["result"]["person"]
    else:
        # something bad happened, don't prefill any fields
        return None
