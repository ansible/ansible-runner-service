from flask_restful import Resource


class BaseResource(Resource):
    state_to_http = {
        "OK": 200,
        "STARTED": 202,
        "INVALID": 400,
        "NOAUTH": 401,
        "FORBIDDEN": 403,
        "NOCONN": 404,
        "NOTFOUND": 404,
        "UNKNOWN": 404,
        "LOCKED": 409,
        "UNSUPPORTED": 415,
        "FAILED": 500,
        "TIMEOUT": 504
    }
