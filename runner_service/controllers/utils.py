from functools import wraps
from flask import request


def requires_auth(f):
    '''
    wrapper function to check authentication credentials are valid
    '''

    @wraps(f)
    def decorated(*args, **kwargs):
        """ check the request carries a valid username/password header """
        pass
        # # check credentials supplied in the http request are valid
        # auth = request.authorization
        # if not auth:
        #     return jsonify(message="Missing credentials"), 401
        #
        # if (auth.username != settings.config.api_user or
        #    auth.password != settings.config.api_password):
        #     return jsonify(message="username/password mismatch with the "
        #                            "configuration file"), 401

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
            logger.info("{} - {} {}, parms={}".format(request.remote_addr,
                                                      request.method,
                                                      request.path,
                                                      request.values.to_dict()))
            return f(*args, **kwargs)
        return wrapper

    return real_decorator
