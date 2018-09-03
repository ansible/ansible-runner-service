from flask_restful import Resource
from .utils import requires_auth, log_request
from ..services.hosts import (get_hosts,
                              add_host,
                              remove_host,
                              get_host_membership
                              )

import logging
logger = logging.getLogger(__name__)


class Hosts(Resource):
    """Return a list of hosts from the inventory - PLACEHOLDER"""

    @requires_auth
    @log_request(logger)
    def get(self):
        """
        GET
        Return all hosts from the ansible inventory
        """

        host_list = get_hosts()

        return {"hosts": host_list}, 200


class HostDetails(Resource):
    """Manage ansible control of a given host - PLACEHOLDER"""

    @requires_auth
    @log_request(logger)
    def get(self, host_name):
        """
        GET {host_name}
        Return the groups that the given host is a member of
        """

        groups = get_host_membership(host_name)

        return {"host": host_name,
                "groups": groups}, 200


class HostMgmt(Resource):
    """Manage ansible control of a given host - PLACEHOLDER"""

    @requires_auth
    @log_request(logger)
    def post(self, host_name, group_name):
        """
        POST hosts/{host_name}/groups/{group_name}
        Add a new host to a group in the ansible inventory
        """

        status = add_host(host_name, group_name)
        if status == 'OK':
            return {"message": "Host {} added to {}".format(host_name,
                                                            group_name)}, 200
        else:
            # TODO more to do here
            return {"message": "Failed to add host - {}".format(status)}, 400

    @requires_auth
    @log_request(logger)
    def delete(self, host_name, group_name):
        """
        DELETE hosts/{host_name}/group/{group_name}
        Remove a host from ansible group
        """

        status = remove_host(host_name, group_name)
        if status == 'OK':
            return {"message": "Host removed from {}".format(group_name)}, 200
        else:
            return {"message": "Unable to remove host: {}".format(status)}, 400
