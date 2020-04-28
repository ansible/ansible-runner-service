from flask_restful import request

from .base import BaseResource
from .utils import log_request
from ..services.hosts import (get_hosts,
                              add_host,
                              remove_host,
                              get_host_membership
                              )
from ..services.utils import APIResponse

import logging
logger = logging.getLogger(__name__)


class Hosts(BaseResource):
    """Return a list of hosts from the inventory"""

    @log_request(logger)
    def get(self):
        """
        GET
        Return all hosts from the ansible inventory

        Example.

        ```
        $ curl -k -i --key ./client.key --cert ./client.crt https://localhost:5001/api/v1/hosts -X GET
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
        """ # noqa

        response = get_hosts()

        return response.__dict__, self.state_to_http[response.status]


class HostDetails(BaseResource):
    """For a given host either show group membership or remove the host"""

    @log_request(logger)
    def get(self, host_name):
        """
        GET {host_name}
        Return the groups that the given host is a member of

        Example.

        ```
        $ curl -k -i --key ./client.key --cert ./client.crt https://localhost:5001/api/v1/hosts/con-1 -X GET
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
        """ # noqa

        response = get_host_membership(host_name)

        return response.__dict__, self.state_to_http[response.status]

    @log_request(logger)
    def delete(self, host_name):
        """
        DELETE {host_name}
        Delete the given host from all ansible roles

        Example.

        ```
        $ curl -k -i --key ./client.key --cert ./client.crt https://localhost:5001/api/v1/hosts/con-1 -X DELETE
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
        """ # noqa

        response = get_host_membership(host_name)
        group_list = response.data['groups']
        for group_name in group_list:
            response = remove_host(host_name, group_name)
            if response.status != 'OK':
                return response.__dict__, self.state_to_http[response.status]

        # removal from all groups was successful
        response.msg = "{} removed from {} group(s) " \
                       "({})".format(host_name,
                                     len(group_list),
                                     ','.join(group_list))
        response.data = {}

        return response.__dict__, self.state_to_http[response.status]


class HostMgmt(BaseResource):
    """Manage ansible control of a given host"""

    def __to_int(self, value):
        """
        Convert value to int, if it's not valid integer return None.
        """ 
        try:
            return int(value)
        except ValueError:
            logger.warn("Port {} is not valid integer number, we will use default SSH port.".format(value))
            return None


    @log_request(logger)
    def post(self, host_name, group_name):
        """
        POST hosts/{host_name}/groups/{group_name}[?others=group2,group3]
        Add a new host to an existing group or groups within the ansible
        inventory

        Example.

        ```
        $ curl -k -i --key ./client.key --cert ./client.crt https://localhost:5001/api/v1/hosts/con-1/groups/dummy -X POST
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

        Example add host with non-standard port:

        ```
        $ curl -k -i --key ./client.key --cert ./client.crt https://localhost:5001/api/v1/hosts/con-1/groups/dummy?port=3333 -X POST
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
        """ # noqa

        valid_parms = ['others', 'port']
        group_list = []
        group_list.append(group_name)
        ssh_port = None

        args = request.args.to_dict()

        if args:
            logger.debug("additional args received")
            if all(p in valid_parms for p in args.keys()):
                if 'others' in args:
                    group_list.extend(args['others'].split(','))
                ssh_port = self.__to_int(args.get('port', 22))
            else:
                r = APIResponse()
                r.status = 'INVALID'
                r.msg = "Supported additional parameters are " \
                        "{}".format(','.join(valid_parms))
                return r.__dict__, self.state_to_http[r.status]

        for group in group_list:
            logger.debug("Adding host {} to group {}".format(host_name, group))
            response = add_host(host_name, group, ssh_port)
            if response.status != 'OK':
                break

        return response.__dict__, self.state_to_http[response.status]

    @log_request(logger)
    def delete(self, host_name, group_name):
        """
        DELETE hosts/{host_name}/group/{group_name}
        Remove a host from an ansible group

        Example.

        ```
        $ curl -k -i --key ./client.key --cert ./client.crt https://localhost:5001/api/v1/hosts/con-1/groups/dummy -X DELETE
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
        """ # noqa

        response = remove_host(host_name, group_name)
        return response.__dict__, self.state_to_http[response.status]
