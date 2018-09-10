
from flask_restful import request     # reqparse
import threading
import logging
import re

from .base import BaseResource
from .utils import requires_auth, log_request

from ..services.playbook import (list_playbooks,
                                 get_status,
                                 start_playbook,
                                 stop_playbook)

from ..services.utils import playbook_exists, APIResponse
from runner_service.cache import runner_cache

logger = logging.getLogger(__name__)
file_mutex = threading.Lock()


class ListPlaybooks(BaseResource):
    """ Return the names of all available playbooks """

    @requires_auth
    @log_request(logger)
    def get(self):
        """
        GET
        Return a list of playbook names

        Example

        ```
        $ curl -i -k https://localhost:5001/api/v1/playbooks
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

    @requires_auth
    @log_request(logger)
    def get(self, play_uuid):
        """
        GET {play_uuid}
        Return the given playbooks current state

        Example

        ```
        $ curl -k -i https://localhost:5001/api/v1/playbooks/1733c3ac-b483-11e8-ad05-c85b7671906d -X get
        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 176
        Server: Werkzeug/0.12.2 Python/3.6.6
        Date: Sun, 09 Sep 2018 22:53:16 GMT

        {
            "status": "OK",
            "msg": "Playbook with UUID 1733c3ac-b483-11e8-ad05-c85b7671906d is active",
            "data": {
                "task_id": 4,
                "task_name": "Step 1"
            }
        }
        ```
        """

        response = get_status(play_uuid)

        return response.__dict__, self.state_to_http[response.status]

    @requires_auth
    @log_request(logger)
    def delete(self, play_uuid):
        """
        DELETE {play_uuid}
        Issue a cancel request to a running playbook

        Example.

        ```
        $ curl -i -k https://localhost:5001/api/v1/playbooks/b7ea3922-b481-11e8-a992-c85b7671906d -X delete
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
    valid_filter = ['limit']

    r = APIResponse()

    if request.content_type != 'application/json':
        r.status, r.msg = "INVALID", "Bad request, endpoint expects a json request/data"
        return r

    vars = request.get_json()
    filter = request.args.to_dict()

    logger.info("Playbook run request for {}, from {}, "
                "parameters: {}".format(playbook_name,
                                        request.remote_addr,
                                        vars))

    # does the playbook exist?
    if not playbook_exists(playbook_name):
        r.status, r.msg = "NOTFOUND", "playbook file not found"
        return r

    response = start_playbook(playbook_name, vars, filter)

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

    @requires_auth
    @log_request(logger)
    def post(self, playbook_name):
        """
        POST {playbook, var1, var2...}
        Start a given playbook, passing a set of variables as json to use for
        the run

        Example

        ```
        $ curl -k -i -H "Content-Type: application/json" --data '{"time_delay":20}' https://localhost:5001/api/v1/playbooks/test.yml -X post
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
        """

        response = _run_playbook(playbook_name)
        return response.__dict__, self.state_to_http[response.status]


class StartTaggedPlaybook(BaseResource):
    """ Start a playbook using tags to control which tasks run """

    @requires_auth
    @log_request(logger)
    def post(self, playbook_name, tags):
        """
        POST {playbook_name}/tags/{tags}
        Start a given playbook using tags to control execution.
        The call is expected to be in json format and may contain json 'payload' to define the variables
        required by the playbook
        Example.

        ```
        $ curl -k -i -H "Content-Type: application/json" --data '{"time_delay":20}' https://localhost:5001/api/v1/playbooks/test.yml/tags/onlyme -X post
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

        pattern = re.compile(r'[a-z0-9]+$')
        if not pattern.match(tags) or tags[-1] == ',':
            _e.status, _e.msg = "INVALID", "Invalid tag syntax"
            return _e.__dict__, self.state_to_http[_e.status]

        response = _run_playbook(playbook_name=playbook_name,
                                 tags=tags)
        return response.__dict__, self.state_to_http[response.status]
