from abc import ABC, abstractmethod
from flask import request, jsonify

# KUMap Exception abstract class
class KUMapCustomException(ABC, Exception):
    @property
    @abstractmethod
    def err_code(self):
        pass

    @property
    @abstractmethod
    def status_code(self):
        pass

    @property
    @abstractmethod
    def err_msg(self):
        pass
    
    @abstractmethod
    def __str__(self):
        pass

# Error: Data format is not JSON
class MissingJsonException(KUMapCustomException):
    @property
    def err_code(self):
        return "10"

    @property
    def status_code(self):
        return 400
    
    @property
    def err_msg(self):
        return "missing json in request"
    
    def __str__(self):
        return self.err_msg

def validate_json():
    if not request.is_json:
        raise MissingJsonException
    
# Error: Required parameter is empty or missing
class MissingParamException(KUMapCustomException):
    def __init__(self, missing_params):
        self.missing_params = missing_params

    @property
    def err_code(self):
        return "11"

    @property
    def status_code(self):
        return 400
    
    @property
    def err_msg(self):
        return f"missing parameters: {', '.join(self.missing_params)}"
    
    def __str__(self):
        return self.err_msg
    
def validate_args_params(*params):
    _params = list(params)
    missing_params = [param for param in _params if param not in request.args]
    if missing_params:
        raise MissingParamException(missing_params)

def validate_json_params(*params):
    _params = list(params)
    missing_params = [param for param in _params if param not in request.json]
    if missing_params:
        raise MissingParamException(missing_params)

# Error: User does not exist
class UserNotExistException(KUMapCustomException):
    @property
    def err_code(self):
        return "20"

    @property
    def status_code(self):
        return 401
    
    @property
    def err_msg(self):
        return "user does not exist"
    
    def __str__(self):
        return self.err_msg

# Error: User password incorrect
class IncorrectPasswordException(KUMapCustomException):
    @property
    def err_code(self):
        return "22"

    @property
    def status_code(self):
        return 401
    
    @property
    def err_msg(self):
        return "incorrect password"
    
    def __str__(self):
        return self.err_msg

