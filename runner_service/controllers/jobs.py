# from flask import request
from flask_restful import request
# import logging
from .utils import log_request
from .base import BaseResource

from ..services.jobs import get_events, get_event
from ..services.utils import APIResponse

import logging
logger = logging.getLogger(__name__)


class ListEvents(BaseResource):
    """Return a list of events within a given playbook run (job) """

    @log_request(logger)
    def get(self, play_uuid=None):
        """
        GET {play_uuid}/events
        Return a list of the event uuid's for the given job(play_uuid). Filtering is also supported, using the
        ?varname=value&varname=value syntax

        Example.

        ```
        $ curl -k -i --key ./client.key --cert ./client.crt https://localhost:5001/api/v1/jobs/9c1714aa-b534-11e8-8c14-aced5c652dd1/events -X GET
        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 1142
        Server: Werkzeug/0.14.1 Python/3.6.5
        Date: Mon, 10 Sep 2018 20:04:53 GMT

        {
            "status": "OK",
            "msg": "",
            "data": {
                "events": {
                    "2-0eaf70cd-0d86-4209-a3ca-73c0633afa27": {
                        "event": "playbook_on_start"
                    },
                    "3-aced5c65-2dd1-7634-7812-00000000000b": {
                        "event": "playbook_on_play_start"
                    },
                    "4-aced5c65-2dd1-7634-7812-00000000000d": {
                        "event": "playbook_on_task_start",
                        "task": "Step 1"
                    },
                    "5-3f6d4b83-df90-401c-9fd7-2b646f00ccfe": {
                        "event": "runner_on_ok",
                        "host": "localhost",
                        "task": "Step 1"
                    },
                    "6-aced5c65-2dd1-7634-7812-00000000000e": {
                        "event": "playbook_on_task_start",
                        "task": "Step 2"
                    },
                    "7-ca1c5d3a-218f-487e-97ec-be5751ac5b40": {
                        "event": "runner_on_ok",
                        "host": "localhost",
                        "task": "Step 2"
                    },
                    "8-7c68cc25-9ccc-4b5c-b4b3-fddaf297e7de": {
                        "event": "playbook_on_stats"
                    }
                },
                "total_events": 7
            }
        }


        ```
        """
        # TODO could the to_dict throw an exception?
        filter = request.args.to_dict()

        _e = APIResponse()

        if not play_uuid:
            _e.status, _e.msg = "INVALID", "playbook uuid missing"
            return _e.__dict__, self.state_to_http[_e.status]

        response = get_events(play_uuid, filter)

        return response.__dict__, self.state_to_http[response.status]


class GetEvent(BaseResource):
    """Return the output of a specific task within a playbook"""

    @log_request(logger)
    def get(self, play_uuid, event_uuid):
        """
        GET {play_uuid, event_uuid}
        Return the json job event data for a given event uuid within a job

        Example.

        ```
        $ curl -k -i --key ./client.key --cert ./client.crt https://localhost:5001/api/v1/jobs/9c1714aa-b534-11e8-8c14-aced5c652dd1/events/2-0eaf70cd-0d86-4209-a3ca-73c0633afa27 -X GET
        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 480
        Server: Werkzeug/0.14.1 Python/3.6.5
        Date: Mon, 10 Sep 2018 20:12:03 GMT

        {
            "status": "OK",
            "msg": "",
            "data": {
                "uuid": "0eaf70cd-0d86-4209-a3ca-73c0633afa27",
                "counter": 2,
                "stdout": "",
                "start_line": 1,
                "end_line": 1,
                "created": "2018-09-10T20:03:40.145870",
                "pid": 27875,
                "event_data": {
                    "pid": 27875,
                    "playbook_uuid": "0eaf70cd-0d86-4209-a3ca-73c0633afa27",
                    "playbook": "test.yml"
                },
                "event": "playbook_on_start"
            }
        }
        ```
        """

        response = get_event(play_uuid, event_uuid)

        return response.__dict__, self.state_to_http[response.status]
