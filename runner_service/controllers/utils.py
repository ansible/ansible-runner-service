from functools import wraps
from flask import request
from ..services.utils import APIResponse
from .base import BaseResource
from runner_service import configuration
import jwt

import logging
logger = logging.getLogger(__name__)


def requires_auth(f):
    '''
    wrapper function to check authentication credentials are valid
    '''

    @wraps(f)
    def decorated(*args, **kwargs):
        """ check the request carries a valid username/password header """

        # if there is a whitelist and if request came from not whitelisted ip
        if configuration.settings.ip_whitelist and request.remote_addr not in configuration.settings.ip_whitelist:
            response = APIResponse()
            response.status, response.msg = "NOAUTH", "Access denied not on whitelist"
            logger.info("{} made a request and is not whitelisted".format(request.remote_addr))
            return response.__dict__, BaseResource.state_to_http[response.status]
        else:  # there is no whitelist let everything through or it came from a whitelisted ip
            # if login move on
            if request.path == "/api/v1/login":
                return f(*args, **kwargs)
            else:  # check for valid token
                token = request.headers.get('Authorization')
                try:
                    jwt.decode(token, 'secret', algorithms='HS256')
                except jwt.DecodeError:
                    response = APIResponse()
                    response.status, response.msg = "NOAUTH", "Access denied invalid token"
                    logger.info("{} made a request without a valid token".format(request.remote_addr))
                    return response.__dict__, BaseResource.state_to_http[response.status]
                except jwt.ExpiredSignatureError:
                    response = APIResponse()
                    response.status, response.msg = "NOAUTH", "Access denied expired token"
                    logger.info("{} made a request with expired valid token".format(request.remote_addr))
                    return response.__dict__, BaseResource.state_to_http[response.status]
                # no exceptions thrown token was good
                return f(*args, **kwargs)

    return decorated


def log_request(logger):
    '''
    wrapper function for HTTP request logging
    '''
    def real_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            """ Look at the request, and log the details """
            # logger.info("{}".format(request.url))
            logger.debug("Request received, content-type :{}".format(request.content_type))
            if request.content_type == 'application/json':
                sfx = ", parms={}".format(request.get_json())
            else:
                sfx = ''
            logger.info("{} - {} {}{}".format(request.remote_addr,
                                              request.method,
                                              request.path,
                                              sfx))
            return f(*args, **kwargs)
        return wrapper

    return real_decorator
