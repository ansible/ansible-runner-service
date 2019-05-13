from flask_restful import request
import yaml

from .base import BaseResource
from .utils import log_request

from ..services.vars import (add_hostvars,
                             remove_hostvars,
                             get_hostvars,
                             get_groupvars,
                             add_groupvars,
                             remove_groupvars)

from ..services.utils import APIResponse

import logging
logger = logging.getLogger(__name__)


class HostVars(BaseResource):
    """Manage host variables for a specific group within the inventory"""

    @log_request(logger)
    def get(self, host_name, group_name):
        """
        GET
        Show variables for a specific host/group

        Example.

        ```
        $ curl -i -k --key client.key --cert client.crt https://localhost:5001/api/v1/hostvars/ceph-1/groups/osds -X GET
        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 171
        Server: Werkzeug/0.12.2 Python/3.6.6
        Date: Thu, 22 Nov 2018 04:00:06 GMT

        {
            "status": "OK",
            "msg": "",
            "data": {
                "vars": {
                    "devices": [
                        "sda",
                        "sdb"
                    ]
                }
            }
        }
        ```
        """ # noqa

        response = get_hostvars(host_name, group_name)

        return response.__dict__, self.state_to_http[response.status]

    @log_request(logger)
    def delete(self, host_name, group_name):
        """
        DELETE
        Remove the host variables from a given group

        Example.

        ```
        $ curl -i -k --key client.key --cert client.crt https://localhost:5001/api/v1/hostvars/ceph-1/groups/osds -X DELETE
        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 129
        Server: Werkzeug/0.12.2 Python/3.6.6
        Date: Thu, 22 Nov 2018 04:01:16 GMT

        {
            "status": "OK",
            "msg": "Vars removed for 'ceph-1' in group 'osds'",
            "data": {
                "hostname": "ceph-1"
            }
        }
        ```
        """ # noqa

        response = remove_hostvars(host_name, group_name)

        return response.__dict__, self.state_to_http[response.status]

    @log_request(logger)
    def post(self, host_name, group_name):
        """
        POST [?type=inventory|file]
        Store host variables.
        By default, host variables are stored in the host_vars subdirectory (type=file) but you may store host vars in the inventory itself by specifying ?type=inventory on the request

        Example.

        ```
        $ curl -i -k --key client.key --cert client.crt -H "Content-Type: application/json" --data '{"devices": ["sda","sdb"]}' https://localhost:5001/api/v1/hostvars/ceph-1/groups/osds -X POST
        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 108
        Server: Werkzeug/0.12.2 Python/3.6.6
        Date: Thu, 22 Nov 2018 03:58:13 GMT

        {
            "status": "OK",
            "msg": "Vars added to ceph-1",
            "data": {
                "hostname": "ceph-1"
            }
        }
        ```
        """ # noqa

        r = APIResponse()
        if request.content_type != 'application/json':
            logger.warning("Invalid request. HOSTVARS POST requests must be "
                           "in JSON format (application/json)")
            r.status, r.msg = "UNSUPPORTED", \
                              "Invalid content-type({}). Use application/" \
                              "json".format(request.content_type)

            return r.__dict__, self.state_to_http[r.status]

        # default for host vars storage
        store_type = 'file'

        vars = request.get_json()
        args = request.args.to_dict()
        if args:
            r_store_type = args.get('type', None)
            if not r_store_type:
                logger.debug("POST request invalid. Only type= is supported")
                r.status, r.msg = "INVALID", \
                                  "Only type=inventory is supported"
                return r.__dict__, self.state_to_http[r.status]

            if r_store_type in ['inventory', 'file']:
                store_type = r_store_type
            else:
                logger.debug("HOSTVARS POST request has invalid type parm")
                r.status, r.msg = "INVALID", \
                                  "type= value must be either inventory or file" # noqa
                return r.__dict__, self.state_to_http[r.status]

        # check that the json object can be converted to YAML
        try:
            yaml.safe_dump(vars)
        except yaml.YAMLError as e:
            logger.error("Unable to convert vars to YAML format : {}".format(e)) # noqa
            r.status, r.msg = "INVALID", \
                              "JSON received could not be converted to YAML"
            return r.__dict__, self.state_to_http[r.status]

        # payload is OK, so let's commit the change
        r = add_hostvars(host_name, group_name, vars, store_type)

        return r.__dict__, self.state_to_http[r.status]


class GroupVars(BaseResource):
    """Manage group variables"""

    @log_request(logger)
    def get(self, group_name):
        """
        GET
        Show variables defined for a specific group

        Example.

        ```
        $ curl -i -k --key client.key --cert client.crt https://localhost:5001/api/v1/groupvars/osds -X GET
        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 217
        Server: Werkzeug/0.12.2 Python/3.6.6
        Date: Tue, 11 Dec 2018 19:36:35 GMT

        {
            "status": "OK",
            "msg": "",
            "data": {
                "vars": {
                    "osd_auto_discovery": false,
                    "osd_objectstore": "bluestore",
                    "osd_scenario": "non-collocated"
                }
            }
        }

        ```
        """ # noqa
        response = get_groupvars(group_name)

        return response.__dict__, self.state_to_http[response.status]

    @log_request(logger)
    def delete(self, group_name):
        """
        DELETE
        Remove the variables from a given group.
        This operation will remove group_vars files for the required group AND also remove any associated group variables stored in the inventory itself.

        Example.

        ```
        $ curl -i -k --key client.key --cert client.crt https://localhost:5001/api/v1/groupvars/osds -X DELETE
        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 83
        Server: Werkzeug/0.12.2 Python/3.6.6
        Date: Tue, 11 Dec 2018 19:41:24 GMT

        {
            "status": "OK",
            "msg": "group vars removed for 'osds'",
            "data": {}
        }
        ```
        """ # noqa

        response = remove_groupvars(group_name)

        return response.__dict__, self.state_to_http[response.status]

    @log_request(logger)
    def post(self, group_name):
        """
        POST [?type=file|inventory]
        Store group variables.
        By default, variables are stored in the group_vars subdirectory (type=file) but you may also store them in the inventory itself by specifying ?type=inventory on the request

        Example.

        ```
        $ curl -i -k --key client.key --cert client.crt -H "Content-Type: application/json" --data '{"osd_auto_discovery": false, "osd_objectstore": "bluestore", "osd_scenario": "non-collocated"}' https://localhost:5001/api/v1/groupvars/osds -X POST
        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 125
        Server: Werkzeug/0.12.2 Python/3.6.6
        Date: Tue, 11 Dec 2018 19:47:31 GMT

        {
            "status": "OK",
            "msg": "Variables written successfully to ./samples/project/group_vars/osds.yml",
            "data": {}
        }
        ```
        """ # noqa

        r = APIResponse()
        if request.content_type != 'application/json':
            logger.warning("Invalid request. GROUPVARS POST requests must be "
                           "in JSON format (application/json)")
            r.status, r.msg = "UNSUPPORTED", \
                              "Invalid content-type({}). Use application/" \
                              "json".format(request.content_type)

            return r.__dict__, self.state_to_http[r.status]

        # default for host vars storage
        store_type = 'file'

        vars = request.get_json()
        args = request.args.to_dict()
        if args:
            r_store_type = args.get('type', None)
            if not r_store_type:
                logger.debug("POST request invalid. Only type= is supported")
                r.status, r.msg = "INVALID", \
                                  "Only type=inventory is supported"
                return r.__dict__, self.state_to_http[r.status]

            if r_store_type in ['inventory', 'file']:
                store_type = r_store_type
            else:
                logger.debug("GROUPVARS POST request has invalid type parm")
                r.status, r.msg = "INVALID", \
                                  "type= value must be either inventory or file" # noqa
                return r.__dict__, self.state_to_http[r.status]

        # check that the json object can be converted to YAML
        try:
            yaml.safe_dump(vars)
        except yaml.YAMLError as e:
            logger.error("Unable to convert vars to YAML format : {}".format(e)) # noqa
            r.status, r.msg = "INVALID", \
                              "JSON received could not be converted to YAML"
            return r.__dict__, self.state_to_http[r.status]

        # payload is OK, so let's commit the change
        r = add_groupvars(group_name, vars, store_type)

        return r.__dict__, self.state_to_http[r.status]
