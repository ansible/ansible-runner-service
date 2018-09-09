from flask_restful import Resource


class BaseResource(Resource):
    state_to_http = {
        "OK": 200,
        "STARTED": 202,
        "INVALID": 400,
        "NOAUTH": 401,
        "NOCONN": 404,
        "NOTFOUND": 404,
        "LOCKED": 409,
        "FAILED": 500,
        "TIMEOUT": 504
    }
