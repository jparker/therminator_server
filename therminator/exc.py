from flask import jsonify
from http import HTTPStatus
from . import app


class ApiError(Exception):
    def __init__(self, message, status_code=HTTPStatus.BAD_REQUEST):
        self.message = message
        self.status_code = status_code

    def as_dict(self):
        return dict(error=self.message)


@app.errorhandler(ApiError)
def handle_api_error(error):
    response = jsonify(error.as_dict())
    response.status_code = error.status_code
    return response
