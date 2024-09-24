from functools import wraps
from app.utils.exceptions import *

def error_handler() -> object:
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            # handle different types of errors and return messages accordingly with status code
            except KUMapCustomException as e:
                return jsonify({
                    "result": "error",
                    "msg": e.err_msg,
                    "err_code": e.err_code
                }), e.status_code
        return wrapped
    return decorator

def validation_request(*params):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            validate_json()
            validate_params(params)
            return f(*args, **kwargs)
        return wrapped
    return decorator