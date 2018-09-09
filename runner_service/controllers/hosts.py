
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
    """Return a list of hosts from the inventory"""

    @requires_auth
    @log_request(logger)
    def get(self):
        """
        GET
        Return all hosts from the ansible inventory

        Example.

        ```
        $ curl -k -i https://localhost:5001/api/v1/hosts -X get
        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 150
        Server: Werkzeug/0.14.1 Python/3.6.6
        Date: Wed, 05 Sep 2018 04:58:31 GMT

        {
            "status": "OK",
            "msg": "",
            "data": {
                "hosts": [
                    "con-1",
                    "con-2",
                    "con-3"
                ]
            }
        }
        ```
        """

        response = get_hosts()

        return response.__dict__, self.state_to_http[response.status]


class HostDetails(BaseResource):
    """Show group membership for a given host"""

    @requires_auth
    @log_request(logger)
    def get(self, host_name):
        """
        GET {host_name}
        Return the groups that the given host is a member of

        Example.

        ```
        $ curl -k -i https://localhost:5001/api/v1/hosts/con-1 -X get
        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 108
        Server: Werkzeug/0.14.1 Python/3.6.6
        Date: Wed, 05 Sep 2018 04:59:05 GMT

        {
            "status": "OK",
            "msg": "",
            "data": {
                "groups": [
                    "osds"
                ]
            }
        }
        ```
        """

        response = get_host_membership(host_name)

        return response.__dict__, self.state_to_http[response.status]


class HostMgmt(BaseResource):
    """Manage ansible control of a given host"""

    @requires_auth
    @log_request(logger)
    def post(self, host_name, group_name):
        """
        POST hosts/{host_name}/groups/{group_name}
        Add a new host to an existing group in the ansible inventory

        Example.

        ```
        $ curl -k -i https://localhost:5001/api/v1/hosts/con-1/groups/dummy -X post
        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 54
        Server: Werkzeug/0.14.1 Python/3.6.6
        Date: Wed, 05 Sep 2018 05:00:33 GMT

        {
            "status": "OK",
            "msg": "",
            "data": {}
        }
        ```
        """

        response = add_host(host_name, group_name)
        return response.__dict__, self.state_to_http[response.status]

    @requires_auth
    @log_request(logger)
    def delete(self, host_name, group_name):
        """
        DELETE hosts/{host_name}/group/{group_name}
        Remove a host from an ansible group

        Example.

        ```
        $ curl -k -i https://localhost:5001/api/v1/hosts/con-1/groups/dummy -X delete
        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 54
        Server: Werkzeug/0.14.1 Python/3.6.6
        Date: Wed, 05 Sep 2018 05:02:03 GMT

        {
            "status": "OK",
            "msg": "",
            "data": {}
        }
        ```
        """

        response = remove_host(host_name, group_name)
        return response.__dict__, self.state_to_http[response.status]
