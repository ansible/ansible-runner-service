
from flask_restful import request     # reqparse
import threading
import logging
import re

from .base import BaseResource
from .utils import log_request

from ..services.playbook import (list_playbooks,
                                 get_status,
                                 start_playbook,
                                 stop_playbook)

from ..services.utils import playbook_exists, APIResponse
from ..inventory import AnsibleInventory
from runner_service.cache import runner_cache

logger = logging.getLogger(__name__)
file_mutex = threading.Lock()


class ListPlaybooks(BaseResource):
    """ Return the names of all available playbooks """

    @log_request(logger)
    def get(self):
        """
        GET
        Return a list of playbook names

        Example.

        ```
        $ curl -i -k --key ./client.key --cert ./client.crt https://localhost:5001/api/v1/playbooks -X GET
        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 179
        Server: Werkzeug/0.12.2 Python/3.6.6
        Date: Sun, 09 Sep 2018 22:51:21 GMT

        {
            "status": "OK",
            "msg": "",
            "data": {
                "playbooks": [
                    "osd-configure.yml",
                    "test.yml",
                    "probe-disks.yml"
                ]
            }
        }
        ```
        """

        response = list_playbooks()

        return response.__dict__, self.state_to_http[response.status]


class PlaybookState(BaseResource):
    """Query the state or cancel a playbook run (by uuid)"""

    @log_request(logger)
    def get(self, play_uuid):
        """
        GET {play_uuid}
        Return the given playbooks current state

        Example.

        ```
        $ curl -k -i --key ./client.key --cert ./client.crt https://localhost:5001/api/v1/playbooks/1733c3ac-b483-11e8-ad05-c85b7671906d -X GET
        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 121
        Server: Werkzeug/0.12.2 Python/3.6.6
        Date: Sun, 23 Sep 2018 22:43:16 GMT

        {
            "status": "OK",
            "msg": "running",
            "data": {
                "task": "RESULTS",
                "last_task_num": 48
            }
        }
        ```
        """

        response = get_status(play_uuid)

        return response.__dict__, self.state_to_http[response.status]

    @log_request(logger)
    def delete(self, play_uuid):
        """
        DELETE {play_uuid}
        Issue a cancel request to a running playbook

        Example.

        ```
        $ curl -i -k --key ./client.key --cert ./client.crt https://localhost:5001/api/v1/playbooks/b7ea3922-b481-11e8-a992-c85b7671906d -X DELETE
        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 75
        Server: Werkzeug/0.12.2 Python/3.6.6
        Date: Sun, 09 Sep 2018 22:43:16 GMT

        {
            "status": "OK",
            "msg": "Cancel request issued",
            "data": {}
        }
        ```
        """
        r = APIResponse()
        if play_uuid not in runner_cache.keys():
            # play_uuid may be valie but it's not actually running
            r.status, r.msg = "NOT ACTIVE", \
                              "playbook with uuid {} is not active".format(play_uuid)
            return r.__dict__, 404

        stop_playbook(play_uuid)
        r.status, r.msg = 'OK', "Cancel request issued"
        return r.__dict__, 200


def _run_playbook(playbook_name, tags=None):
    """
    Run the given playbook
    """
    # TODO Move this function to the service package (services.playbook)

    # TODO We should use a list like this to restrict the query we support
    valid_filter = ['limit', 'check']

    r = APIResponse()

    if not request.content_type.startswith('application/json'):
        logger.warning("Invalid request type. Playbook POST requests must be "
                       "in application/json format")
        r.status, r.msg = "UNSUPPORTED", \
                          "Invalid content-type({}). Use application/" \
                          "json".format(request.content_type)
        return r
    try:
        vars = request.get_json()
    except Exception as e:
        r.status, r.msg = "INVALID", "Failed to decode JSON object: {}".format(e)
        logger.error(r)
        return r
    filter = request.args.to_dict()
    if not all([_k in valid_filter for _k in filter.keys()]):
        r.status, r.msg = "INVALID", "Bad request, supported " \
                          "filters are: {}".format(','.join(valid_filter))
        return r

    if 'limit' in filter:

        target_hosts = filter['limit'].split(',')
        inv_hosts = AnsibleInventory().hosts
        logger.debug("Checking host limit against the inventory")
        if all([_h in inv_hosts for _h in target_hosts]):
            logger.debug("hosts in the limit list match the inventory")

        else:
            logger.error("limit hosts don't match with the inventory")
            # host(s) provided are not all in the inventory
            r.status, r.msg = "INVALID", \
                              "Host(s) provided not in Ansible inventory"
            return r

    logger.info("Playbook run request for {}, from {}, "
                "parameters: {}".format(playbook_name,
                                        request.remote_addr,
                                        vars))

    # does the playbook exist?
    if not playbook_exists(playbook_name):
        r.status, r.msg = "NOTFOUND", "playbook file not found"
        return r

    response = start_playbook(playbook_name, vars, filter, tags)

    play_uuid = response.data.get('play_uuid', None)
    status = response.data.get('status', None)
    msg = ("Playbook {}, UUID={} initiated :"
           " status={}".format(playbook_name,
                               play_uuid,
                               status))

    if status in ['started', 'starting', 'running', 'successful']:
        logger.info(msg)
    else:
        logger.error(msg)

    if play_uuid:
        r.status, r.msg, r.data = "STARTED", status, {"play_uuid": play_uuid}
        return r
    else:
        r.status, r.msg = "FAILED", "Runner thread failed to start"
        return r


class StartPlaybook(BaseResource):
    """ Start a playbook by name, returning the play's uuid """

    @log_request(logger)
    def post(self, playbook_name):
        """
        POST {playbook, var1, var2...}

        Example 1.

        Start a given playbook, passing a set of variables as json to use for
        the run

        ```
        $ curl -k -i --key ./client.key --cert ./client.crt -H "Content-Type: application/json" --data '{"time_delay":20}' https://localhost:5001/api/v1/playbooks/test.yml -X POST
        HTTP/1.0 202 ACCEPTED
        Content-Type: application/json
        Content-Length: 132
        Server: Werkzeug/0.12.2 Python/3.6.6
        Date: Sun, 09 Sep 2018 22:52:55 GMT

        {
            "status": "STARTED",
            "msg": "starting",
            "data": {
                "play_uuid": "1733c3ac-b483-11e8-ad05-c85b7671906d"
            }
        }
        ```

        Example 2:

        Limiting the playbook execution to certain hosts.
        (Note: Hosts must be included previously in inventory)

        ```
        $ curl -k -i --key ./client.key --cert ./client.crt -H "Content-Type: application/json" --data '{"time_delay":20}' https://192.168.121.1:5001/api/v1/playbooks/test.yml?limit=host0,host1 -X POST
        HTTP/1.1 202 ACCEPTED
        Server: nginx/1.12.2
        Date: Wed, 12 Jun 2019 09:59:47 GMT
        Content-Type: application/json
        Content-Length: 104
        Connection: keep-alive

        {
            "status": "STARTED",
            "msg": "starting",
            "data": {"play_uuid": "cfbdd41e-8cf8-11e9-9154-2016b900e38f"
            }
        }

        ```

        Example 3:

        Running the playbook execution in check(dry) mode.

        ```
        $ curl -k -i --key ./client.key --cert ./client.crt -H "Content-Type: application/json" --data '{"time_delay":20}' https://192.168.121.1:5001/api/v1/playbooks/test.yml?check=true -X POST
        HTTP/1.1 202 ACCEPTED
        Server: nginx/1.12.2
        Date: Wed, 12 Jun 2019 09:59:47 GMT
        Content-Type: application/json
        Content-Length: 104
        Connection: keep-alive

        {
            "status": "STARTED",
            "msg": "starting",
            "data": {"play_uuid": "cfbdd41e-8cf8-11e9-9154-2016b900e38f"
            }
        }

        ```

        """

        response = _run_playbook(playbook_name)
        return response.__dict__, self.state_to_http[response.status]


class StartTaggedPlaybook(BaseResource):
    """ Start a playbook using tags to control which tasks run """

    @log_request(logger)
    def post(self, playbook_name, tags):
        """
        POST {playbook_name}/tags/{tags}
        Start a given playbook using tags to control execution.
        The call is expected to be in json format and may contain json 'payload' to define the variables
        required by the playbook
        The {tags} component is a list of one or more tags separated by comma
        Example.

        ```
        $ curl -k -i --key ./client.key --cert ./client.crt -H "Content-Type: application/json" --data '{"time_delay":20}' https://localhost:5001/api/v1/playbooks/test.yml/tags/onlyme -X POST
        HTTP/1.0 202 ACCEPTED
        Content-Type: application/json
        Content-Length: 132
        Server: Werkzeug/0.12.2 Python/3.6.6
        Date: Sun, 09 Sep 2018 22:59:40 GMT

        {
            "status": "STARTED",
            "msg": "starting",
            "data": {
                "play_uuid": "0884ec40-b484-11e8-b114-c85b7671906d"
            }
        }
        ```
        """
        _e = APIResponse()
        if not tags:
            _e.status, _e.msg = "INVALID", "tag based run requested, but tags are missing?"
            return _e.__dict__, self.state_to_http[_e.status]

        pattern = re.compile(r'[a-zA-Z0-9\,]+$')
        if not pattern.match(tags) or tags[-1] == ',':
            _e.status, _e.msg = "INVALID", "Invalid tag syntax"
            return _e.__dict__, self.state_to_http[_e.status]

        response = _run_playbook(playbook_name=playbook_name,
                                 tags=tags)
        return response.__dict__, self.state_to_http[response.status]
