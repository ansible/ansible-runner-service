
from flask_restful import Resource, request     # reqparse
import threading
import logging
import os
import re

from .utils import requires_auth, log_request
from ..services.playbook import list_playbooks
from ..services.playbook import get_status, start_playbook
from ..services.utils import playbook_exists
from runner_service import configuration
from runner_service.utils import TimeOutLock

logger = logging.getLogger(__name__)
file_mutex = threading.Lock()


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


def _run_playbook(playbook_name, tags=None):
    """
    Run the given playbook
    """

    # TODO We should use a list like this to restrict the query we support
    valid_filter = ['limit']

    if request.content_type != 'application/json':
        return {"message": "Bad request, endpoint expects a json request/data"}, 400

    vars = request.get_json()
    filter = request.args.to_dict()

    logger.info("Playbook run request for {}, from {}, "
                "parameters: {}".format(playbook_name,
                                        request.remote_addr,
                                        vars))

    # does the playbook exist?
    if not playbook_exists(playbook_name):
        return {"message": "playbook file not found"}, 404

    if tags:
        # overwrite the env/cmdline file with the required tags
        # Using a threading.Condition based lock to provide a timeout. If the
        # timeout is reached, we can request the caller tries again later
        f_lock = TimeOutLock(file_mutex)
        ready = f_lock.wait(2)
        if ready:
            cmd_file = os.path.join(configuration.settings.playbooks_root_dir,
                                    "env", "cmdline")
            logger.debug("Attempting to update {}".format(cmd_file))

            try:
                with open(cmd_file, 'w') as cmdline:
                    cmdline.write(" --tags {}".format(tags))
            except IOError:
                logger.error("TAGS requested for {}, but unable to create"
                             " env/cmdline file".format(playbook_name))
            else:
                logger.debug("Update of {} successful".format(cmd_file))
        else:
            # timeout hit acquiring the file mutex
            return {"message": "timed out ({}secs) waiting to update "
                               "env/cmdline, try again later"}, 503

    play_uuid, status = start_playbook(playbook_name, vars, filter)
    if tags:
        f_lock.reset()

    msg = ("Playbook {}, UUID={} initiated :"
           " status={}".format(playbook_name,
                               play_uuid,
                               status))

    if status in ['started', 'starting', 'running', 'successful']:
        logger.info(msg)
    else:
        logger.error(msg)

    if play_uuid:
        return {"play_uuid": play_uuid,
                "status": status}, 202
    else:
        return {"message": "Runner thread failed to start"}, 500


class StartPlaybook(Resource):
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
        [paul@rh460p ~]$ curl -k -i -H "Content-Type: application/json" --data '{"time_delay": 10}' \
        https://localhost:5001/api/v1/playbooks/test.yml -X POST
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

        response, status_code = _run_playbook(playbook_name)

        return response, status_code


class StartTaggedPlaybook(Resource):
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
        [paul@rh460p ~] curl -k -i -H "Content-Type: application/json" --data '{"time_delay": 20}' https://localhost:5001/api/v1/playbooks/test.yml/tags/onlyme -X POST
        HTTP/1.0 202 ACCEPTED
        Content-Type: application/json
        Content-Length: 86
        Server: Werkzeug/0.12.2 Python/2.7.15
        Date: Wed, 22 Aug 2018 00:04:35 GMT

        {
            "play_uuid": "f405051e-a59e-11e8-b1be-c85b7671906d",
            "status": "running"
        }
        ```

        """

        if not tags:
            return {"message": "tag based run requested, but tags are missing?"}, 400

        pattern = re.compile(r'[a-z0-9]+$')
        if not pattern.match(tags) or tags[-1] == ',':
            return {"message": "Invalid tag syntax"}, 400

        response, status_code = _run_playbook(playbook_name=playbook_name,
                                              tags=tags)

        return response, status_code
