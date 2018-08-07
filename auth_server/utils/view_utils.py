from functools import wraps
from flask import request


def json_or_400(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not request.is_json:
            return "Request body should be valid json", 400
        else:
            return fn(*args, **kwargs)
    return wrapper
