from functools import wraps
from flask import request, jsonify
from ..services.utils import APIResponse
from .base import BaseResource
from runner_service import configuration

import logging
logger = logging.getLogger(__name__)


def requires_auth(f):
    '''
    wrapper function to check authentication credentials are valid
    '''

    @wraps(f)
    def decorated(*args, **kwargs):
        """ check the request carries a valid username/password header """


        # # check credentials supplied in the http request are valid
        # auth = request.authorization
        # if not auth:
        #     return jsonify(message="Missing credentials"), 401
        #
        # if (auth.username != settings.config.api_user or
        #    auth.password != settings.config.api_password):
        #     return jsonify(message="username/password mismatch with the "
        #                            "configuration file"), 401

        #if there is a whitelist and if response came from not whitelisted ip
        if configuration.settings.ip_whitelist and request.remote_addr not in configuration.settings.ip_whitelist:
            responce = APIResponse()
            responce.status, responce.msg = "NOAUTH", "Access denied not on whitelist"
            logger.info("{} made a requested and is not whitelisted".format(request.remote_addr))
            return responce.__dict__, BaseResource.state_to_http[responce.status]
        else:# there is no whitelist let everything through or it came from a whitelisted ip
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
