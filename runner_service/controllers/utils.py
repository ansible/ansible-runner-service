from functools import wraps
from flask import request
from ..services.utils import APIResponse
from .base import BaseResource
from runner_service import configuration

import logging
logger = logging.getLogger(__name__)

def log_request(logger):
    '''
    wrapper function for HTTP request logging
    '''
    def real_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            """ Look at the request, and log the details """
            # logger.info("{}".format(request.url))
            logger.debug("Request received, content-type :"
                         "{}".format(request.content_type))
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
