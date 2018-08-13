from flask_restful import Resource
from .utils import requires_auth

import logging
logger = logging.getLogger(__name__)


class Hosts(Resource):
    """Return a list of hosts from the inventory - PLACEHOLDER"""

    @requires_auth
    def get(self):
        """
        GET
        Return a list of hosts known to the ansible inventory - NOT IMPLEMENTED
        """

        return 501
