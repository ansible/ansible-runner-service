# import os
# import logging
from flask import Flask
from flask_restful import Api

from .controllers import (ListPlaybooks,
                          PlaybookState,
                          StartPlaybook,
                          API,
                          ListEvents,
                          GetEvent,
                          Hosts,
                          )
import logging
logger = logging.getLogger(__name__)


def create_app():

    app = Flask("runner_service")

    api = Api(app)

    api.add_resource(ListPlaybooks, "/api/v1/playbooks")
    api.add_resource(StartPlaybook, "/api/v1/playbooks/<playbook_name>")
    api.add_resource(PlaybookState, "/api/v1/playbooks/<play_uuid>")
    api.add_resource(ListEvents, "/api/v1/jobs/<play_uuid>/events")
    api.add_resource(GetEvent, "/api/v1/jobs/<play_uuid>/events/<event_uuid>")

    api.add_resource(Hosts, "/api/v1/hosts")
    api.add_resource(API, "/api")

    # push the app into the API class, so it can walk the
    # API endpoints.
    API.app = app

    return app
