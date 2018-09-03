
from runner_service import AnsibleInventory, configuration

import logging
logger = logging.getLogger(__name__)


def add_host(host_name, group_name):
    # TODO: lock inventory?

    inventory = AnsibleInventory()
    if group_name not in inventory.groups:
        # invalid request no such group
        return

    group_members = inventory.group_show(group_name)
    if host_name in group_members:
        # host already in that group!
        return

    # At this point, the group is valid, and the host requested isn't already
    # in it, so proceed

    # TODO is name an IP - if so is it valid?
    # TODO if it's a name, does it resolve with DNS?
    # TODO check ssh connection is valid first (if host isn't in inventory.hosts)

    inventory.host_add(group_name, host_name)
    inventory.save()
    return 'OK'


def remove_host(host_name, group_name):
    inventory = AnsibleInventory()
    if group_name not in inventory.groups or \
      host_name not in inventory.group_show(group_name):
        # invalid request
        return "Invalid Request"

    # At this point the removal is ok
    inventory.host_remove(group_name, host_name)
    inventory.save()

    return "OK"


def get_hosts():
    inventory = AnsibleInventory()
    return inventory.hosts


def get_host_membership(host_name):
    inventory = AnsibleInventory()
    return inventory.host_show(host_name)
