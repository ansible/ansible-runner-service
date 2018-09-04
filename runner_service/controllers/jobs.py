import os
# from flask import request
from flask_restful import request
# import logging
from .utils import requires_auth, log_request
from .base import BaseResource

from ..services.jobs import get_events, get_event
from ..services.utils import build_pb_path, APIResponse

import logging
logger = logging.getLogger(__name__)


class ListEvents(BaseResource):
    """Return a list of events within a given playbook run (job) """

    @requires_auth
    @log_request(logger)
    def get(self, play_uuid=None):
        """
        GET {play_uuid}/events
        Return a list of the event uuid's for the given job(play_uuid). Filtering is also supported, using the
        ?varname=value&varname=value syntax
        Example

        ```
        [paul@rh460p ~]$ curl -k -i https://localhost:5001/api/v1/jobs/da069894-99d7-11e8-9ffc-c85b7671906d/events  -X GET
        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 448
        Server: Werkzeug/0.12.2 Python/2.7.15
        Date: Tue, 07 Aug 2018 01:51:45 GMT

        {
            "job_events": [
                "10-c85b7671-906d-a14a-6984-000000000005",
                "11-c85b7671-906d-a14a-6984-000000000007",
                "12-74766024-2bc7-477a-ab67-86ac09221992",
                "13-c85b7671-906d-a14a-6984-000000000008",
                "14-ea7d6fef-9e5a-497a-9f22-2fba98b30304",
                "15-50bf2a7e-1a28-495a-8360-87303fbfe9f3",
                "9-32737fb7-3688-4146-84c4-97d2faf13ad6"
            ],
            "play_uuid": "da069894-99d7-11e8-9ffc-c85b7671906d"
        }


        ```
        """
        # TODO could the to_dict throw an exception?
        filter = request.args.to_dict()

        _e = APIResponse()

        if not play_uuid:
            _e.status, _e.msg = "INVALID", "playbook uuid missing"
            return _e.__dict__, self.state_to_http[_e.status]

        pb_path = build_pb_path(play_uuid)

        if not os.path.exists(pb_path):
            _e.status, _e.msg = "NOTFOUND", "playbook uuid given does not exist"
            return _e.__dict__, self.state_to_http[_e.status]

        response = get_events(pb_path, filter)

        return response.__dict__, self.state_to_http[response.status]


class GetEvent(BaseResource):
    """Return the output of a specific task within a playbook"""

    @requires_auth
    @log_request(logger)
    def get(self, play_uuid, event_uuid):
        """
        GET {play_uuid, event_uuid}
        Return the json job event data for a given event uuid within a job
        Example

        ```
        [paul@rh460p ~]$ curl -k -i https://localhost:5001/api/v1/jobs/da069894-99d7-11e8-9ffc-c85b7671906d/events/14-ea7d6fef-9e5a-497a-9f22-2fba98b30304  -X GET
        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 2710
        Server: Werkzeug/0.12.2 Python/2.7.15
        Date: Tue, 07 Aug 2018 01:52:20 GMT

        {
            "data": {
                "counter": 14,
                "created": "2018-08-07T00:22:00.284164",
                "end_line": 16,
                "event": "runner_on_ok",
                "event_data": {
                    "event_loop": null,
                    "host": "localhost",
                    "pid": 18708,
                    "play": "test Playbook",
                    :
                    :
                },
                "pid": 18708,
                "start_line": 15,
                "stdout": "\u001b[0;33mchanged: [localhost]\u001b[0m",
                "uuid": "ea7d6fef-9e5a-497a-9f22-2fba98b30304"
            },
            "event_uuid": "14-ea7d6fef-9e5a-497a-9f22-2fba98b30304",
            "play_uuid": "da069894-99d7-11e8-9ffc-c85b7671906d"
        }
        ```
        """

        pb_path = build_pb_path(play_uuid)

        response = get_event(pb_path, event_uuid)

        return response.__dict__, self.state_to_http[response.status]
