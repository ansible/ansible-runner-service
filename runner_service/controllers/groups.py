

from .base import BaseResource
from .utils import log_request
from ..services.groups import (get_groups,
                               add_group,
                               remove_group,
                               get_group_members
                               )


import logging
logger = logging.getLogger(__name__)


class ListGroups(BaseResource):
    """List all the defined groups in the inventory"""

    @log_request(logger)
    def get(self):
        """
        GET
        Show all groups defined in the 'inventory'

        Example.

        ```
        $ curl -k -i --key ./client.key --cert ./client.crt https://localhost:5001/api/v1/groups -X GET
        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 108
        Server: Werkzeug/0.14.1 Python/3.6.6
        Date: Wed, 05 Sep 2018 04:48:35 GMT

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

        response = get_groups()
        return response.__dict__, self.state_to_http[response.status]


class ManageGroups(BaseResource):
    """
    Manage groups within the inventory
    """

    @log_request(logger)
    def get(self, group_name):
        """
        GET {group_name}
        Show members within a given Ansible host group

        Example.

        ```
        $ curl -k -i --key ./client.key --cert ./client.crt https://localhost:5001/api/v1/groups/osds -X GET
        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 152
        Server: Werkzeug/0.14.1 Python/3.6.6
        Date: Wed, 05 Sep 2018 05:17:57 GMT

        {
            "status": "OK",
            "msg": "",
            "data": {
                "members": [
                    "con-1",
                    "con-2",
                    "con-3"
                ]
            }
        }
        ```
        """

        response = get_group_members(group_name)
        return response.__dict__, self.state_to_http[response.status]


    @log_request(logger)
    def post(self, group_name):
        """
        POST {group_name}
        Add a new group to the inventory

        Example.

        ```
        $ curl -k -i --key ./client.key --cert ./client.crt https://localhost:5001/api/v1/groups/dummy -X POST
        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 71
        Server: Werkzeug/0.14.1 Python/3.6.6
        Date: Wed, 05 Sep 2018 04:54:51 GMT

        {
            "status": "OK",
            "msg": "Group dummy added",
            "data": {}
        }
        ```
        """

        response = add_group(group_name)

        return response.__dict__, self.state_to_http[response.status]


    @log_request(logger)
    def delete(self, group_name):
        """
        DELETE {group_name}
        Remove a group (and all related hosts) from the inventory

        Example.

        ```
        $ curl -k -i --key ./client.key --cert ./client.crt https://localhost:5001/api/v1/groups/dummy -X DELETE
        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 73
        Server: Werkzeug/0.14.1 Python/3.6.6
        Date: Wed, 05 Sep 2018 04:56:08 GMT

        {
            "status": "OK",
            "msg": "Group dummy removed",
            "data": {}
        }
        ```
        """

        response = remove_group(group_name)

        return response.__dict__, self.state_to_http[response.status]
