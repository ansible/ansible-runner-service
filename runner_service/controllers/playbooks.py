
from flask_restful import Resource, request     # reqparse
from .utils import requires_auth, log_request
from ..services.playbook import list_playbooks
from ..services.playbook import get_status, start_playbook
from ..services.utils import playbook_exists
import logging
logger = logging.getLogger(__name__)


class ListPlaybooks(Resource):
    """ Return the names of all available playbooks """

    @requires_auth
    @log_request(logger)
    def get(self):
        """
        GET
        Return a list of playbook names
        Example

        ```
        [paul@rh460p ~]$ curl -k -i https://localhost:5001/api/v1/playbooks -X GET
        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 48
        Server: Werkzeug/0.12.2 Python/2.7.15
        Date: Mon, 06 Aug 2018 02:51:37 GMT

        {
            "playbooks": [
                "test.yml"
            ]
        }
        ```
        """

        playbook_names = list_playbooks()

        if playbook_names:
            return {"playbooks": playbook_names}, 200
        else:
            return {"message": "No playbook files found"}, 404


class PlaybookState(Resource):
    """ Query the state of a playbook run, by uuid """

    @requires_auth
    @log_request(logger)
    def get(self, play_uuid):
        """
        GET {play_uuid}
        Return the given playbooks current state
        Example

        ```
        [paul@rh460p ~]$ curl -k -i https://localhost:5001/api/v1/playbooks/f39069aa-9f3d-11e8-852f-c85b7671906d -X GET
        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 134
        Server: Werkzeug/0.12.2 Python/2.7.15
        Date: Mon, 13 Aug 2018 21:15:34 GMT

        {
            "play_uuid": "f39069aa-9f3d-11e8-852f-c85b7671906d",
            "status": "running",
            "task_id": 13,
            "task_name": "Step 2"
        }

        ```
        """

        status = get_status(play_uuid)

        if status:
            status['play_uuid'] = play_uuid
            return status, 200
        else:
            return {"message": "playbook run with uuid {}"
                               " not found".format(play_uuid)}, 404


class StartPlaybook(Resource):
    """ Start a playbook by name, returning the play's uuid """

    @requires_auth
    @log_request(logger)
    def post(self, playbook_name):
        """
        POST {playbook, var1, var2...}
        Start a given playbook, passing a set of variables to use for the run
        Example

        ```
        [paul@rh460p ~]$ curl -k -i https://localhost:5001/api/v1/playbooks/test.yml -d "time_delay=10" -X POST
        HTTP/1.0 202 ACCEPTED
        Content-Type: application/json
        Content-Length: 86
        Server: Werkzeug/0.12.2 Python/2.7.15
        Date: Tue, 07 Aug 2018 00:21:38 GMT

        {
            "play_uuid": "da069894-99d7-11e8-9ffc-c85b7671906d",
            "status": "started"
        }
        ```
        """

        vars = request.form.to_dict()

        logger.info("Playbook request for {}, from {}, "
                    "parameters: {}".format(playbook_name,
                                            request.remote_addr,
                                            vars))

        # does the playbook exist?
        if not playbook_exists(playbook_name):
            return {"message": "playbook file not found"}, 404

        play_uuid, status = start_playbook(playbook_name, vars)
        if play_uuid:
            return {"play_uuid": play_uuid,
                    "status": status}, 202
        else:
            return {"message": "Runner thread failed to start"}, 500
