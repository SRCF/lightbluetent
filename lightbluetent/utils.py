import uuid

def gen_unique_string():
    return str(uuid.uuid4()).replace("-", "")


