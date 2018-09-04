

from .base import BaseResource
from .utils import requires_auth, log_request
from ..services.groups import (get_groups,
                               add_group,
                               remove_group,
                               get_group_members
                               )


import logging
logger = logging.getLogger(__name__)


class ListGroups(BaseResource):
    """List all the defined groups in the inventory"""

    @requires_auth
    @log_request(logger)
    def get(self):
        """
        Show all host groups
        """

        response = get_groups()
        return response.__dict__, self.state_to_http[response.status]


class ManageGroups(BaseResource):
    """
    Manage groups within the inventory
    """

    @requires_auth
    @log_request(logger)
    def get(self, group_name):
        """
        Show members within a given Ansible host group
        """

        response = get_group_members(group_name)
        return response.__dict__, self.state_to_http[response.status]

    @requires_auth
    @log_request(logger)
    def post(self, group_name):
        """
        Add a new group to the inventory
        """

        response = add_group(group_name)

        return response.__dict__, self.state_to_http[response.status]

    @requires_auth
    @log_request(logger)
    def delete(self, group_name):
        """
        Remove a group (and all related hosts) from the inventory
        """

        response = remove_group(group_name)

        return response.__dict__, self.state_to_http[response.status]
