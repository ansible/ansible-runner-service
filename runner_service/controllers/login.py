from flask_restful import request
import logging
from .utils import requires_auth, log_request
from .base import BaseResource
from ..services.utils import APIResponse
from runner_service import configuration
import jwt
import datetime

logger = logging.getLogger(__name__)


class Login(BaseResource):
    """Authenticate user and provide token"""

    @requires_auth
    @log_request(logger)
    def get(self):
        """
        GET {username, password}
        Login to get token

        Example.

        ```
        $ curl -k -i -H "Content-Type: application/json" --data '{"username":"admin", "password": "admin"}' https://localhost:5001/api/v1/login -X get
        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 198
        Server: Werkzeug/0.14.1 Python/3.6.5
        Date: Tue, 18 Sep 2018 18:29:18 GMT

        {
            "status": "OK",
            "msg": "Token returned",
            "data": {
                "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE1MzczODE3NTh9.6H5cRsNhbWM40T4VsBKH6bYSrINUZHnnKhjGLJqZtVQ"
            }
        }
        ```
        """

        # check for json data
        if request.content_type != 'application/json':
            r = APIResponse()
            r.status, r.msg = "INVALID", "Bad request, endpoint expects a json " \
                                         "request/data"
            return r

        # get data and check for expected values
        user_info = request.get_json()
        if 'username' in user_info and 'password' in user_info:
            # compare json supplied user/pass to config user/pass
            for user, password in configuration.settings.passwords.items():
                if user_info['username'] == user:
                    if user_info['password'] == password:
                        # got a valid user and pass
                        # generate token
                        exp = datetime.datetime.utcnow() + datetime.timedelta(hours=configuration.settings.token_hours)
                        encoded = jwt.encode({'exp': exp}, configuration.settings.token_secret, algorithm='HS256')
                        token = encoded.decode('utf-8')

                        response = APIResponse()
                        response.status, response.msg, response.data = "OK", "Token returned", {"token": token}
                        return response.__dict__, self.state_to_http[response.status]
                    else:
                        # valid user but pass is wrong
                        response = APIResponse()
                        response.status, response.msg = "NOAUTH", "Access denied invalid login"
                        logger.info("{} tried to login with invalid password".format(request.remote_addr))
                        return response.__dict__, BaseResource.state_to_http[response.status]
            # no valid user found
            response = APIResponse()
            response.status, response.msg = "NOAUTH", "Access denied invalid login"
            logger.info("{} tried to login with invalid user".format(request.remote_addr))
            return response.__dict__, BaseResource.state_to_http[response.status]
        else:  # did not get expected data in json
            response = APIResponse()
            response.status, response.msg = "NOAUTH", "Access denied invalid data"
            return response.__dict__, BaseResource.state_to_http[response.status]
