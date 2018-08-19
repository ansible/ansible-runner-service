from flask_restful import Resource
from .utils import requires_auth, log_request

import logging
logger = logging.getLogger(__name__)


class Hosts(Resource):
    """Return a list of hosts from the inventory - PLACEHOLDER"""

    @requires_auth
    @log_request(logger)
    def get(self):
        """
        GET
        Return a list of hosts known to the ansible inventory - NOT IMPLEMENTED
        """

        return {"message": "NOT Implemented"}, 501


class HostMgmt(Resource):
    """Manage ansible control of a given host - PLACEHOLDER"""

    @requires_auth
    @log_request(logger)
    def get(self):
        """
        GET {host_name}
        Return the groups that the given host is a member of
        """
        return {"message": "NOT Implemented"}, 501

    @requires_auth
    @log_request(logger)
    def post(self):
        """
        POST {host_name}
        Add a new host to the ansible configuration
        """
        return {"message": "NOT Implemented"}, 501

    @requires_auth
    @log_request(logger)
    def delete(self):
        """
        POST {host_name}
        Remove a host from ansible control
        """
        return {"message": "NOT Implemented"}, 501


class HostUpdate(Resource):
    """Manage group membership of an existing host - PLACEHOLDER"""

    @requires_auth
    @log_request(logger)
    def put(self):
        """
        PUT {host_name, group_name}
        Update the groups a given host belongs to
        """
        return {"message": "NOT Implemented"}, 501
