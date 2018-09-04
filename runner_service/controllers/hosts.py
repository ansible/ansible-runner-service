
from .base import BaseResource
from .utils import requires_auth, log_request
from ..services.hosts import (get_hosts,
                              add_host,
                              remove_host,
                              get_host_membership
                              )

import logging
logger = logging.getLogger(__name__)


class Hosts(BaseResource):
    """Return a list of hosts from the inventory - PLACEHOLDER"""

    @requires_auth
    @log_request(logger)
    def get(self):
        """
        GET
        Return all hosts from the ansible inventory
        """

        response = get_hosts()

        return response.__dict__, self.state_to_http[response.status]


class HostDetails(BaseResource):
    """Manage ansible control of a given host - PLACEHOLDER"""

    @requires_auth
    @log_request(logger)
    def get(self, host_name):
        """
        GET {host_name}
        Return the groups that the given host is a member of
        """

        response = get_host_membership(host_name)

        return response.__dict__, self.state_to_http[response.status]


class HostMgmt(BaseResource):
    """Manage ansible control of a given host - PLACEHOLDER"""

    @requires_auth
    @log_request(logger)
    def post(self, host_name, group_name):
        """
        POST hosts/{host_name}/groups/{group_name}
        Add a new host to a group in the ansible inventory
        """

        response = add_host(host_name, group_name)
        return response.__dict__, self.state_to_http[response.status]

    @requires_auth
    @log_request(logger)
    def delete(self, host_name, group_name):
        """
        DELETE hosts/{host_name}/group/{group_name}
        Remove a host from ansible group
        """

        response = remove_host(host_name, group_name)
        return response.__dict__, self.state_to_http[response.status]
