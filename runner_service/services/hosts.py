import os

from runner_service import AnsibleInventory, configuration
from .utils import APIResponse
from ..utils import ssh_connect_ok, fread

import logging
logger = logging.getLogger(__name__)


def add_host(host_name, group_name, ssh_port=None):
    r = APIResponse()
    r.data = {"hostname": host_name}
    inventory = AnsibleInventory(excl=True)
    if not inventory.loaded:
        r.status, r.msg = "LOCKED", \
                          "Unable to lock the inventory file, try later"
        return r

    if group_name not in inventory.groups:
        # invalid request no such group
        r.status, r.msg = "INVALID", "No such group found in the inventory"
        inventory.unlock()
        return r

    group_members = inventory.group_show(group_name)
    if host_name in group_members:
        # host already in that group!
        r.status, r.msg = "OK", \
                          "Host already in the group {}".format(group_name)
        inventory.unlock()
        return r

    # At this point, the group is valid, and the host requested isn't already
    # in it, so proceed

    # TODO is name an IP - if so is it valid?
    # TODO if it's a name, does it resolve with DNS?
    if configuration.settings.ssh_checks:
        ssh_ok, msg = ssh_connect_ok(host_name, port=ssh_port)
        if ssh_ok:
            logger.info("SSH - {}".format(msg))
        else:
            logger.error("SSH - {}".format(msg))
            error_info = msg.split(':', 1)
            if error_info[0] == "NOAUTH":
                pub_key_file = os.path.join(configuration.settings.playbooks_root_dir,  # noqa
                                            "env/ssh_key.pub")
                r.data = {"pub_key": fread(pub_key_file)}

            r.status, r.msg = error_info

            inventory.unlock()
            return r
    else:
        logger.warning("Skipped SSH connection test for {}".format(host_name))
        r.msg = 'skipped SSH checks due to ssh_checks disabled by config'

    inventory.host_add(group_name, host_name, ssh_port)
    r.status = "OK"
    r.msg = "{} added".format(host_name)

    return r


def remove_host(host_name, group_name):
    r = APIResponse()
    inventory = AnsibleInventory(excl=True)

    if not inventory.loaded:
        r.status, r.msg = "LOCKED", "Unable to lock the inventory file, " \
                                    "try later"
        return r

    if (group_name not in inventory.groups or
       host_name not in inventory.group_show(group_name)):
        # invalid request
        r.status, r.msg = "INVALID", "No such group found in the inventory"
        inventory.unlock()
        return r

    # At this point the removal is ok
    inventory.host_remove(group_name, host_name)
    r.status = "OK"

    return r


def get_hosts():
    r = APIResponse()
    inventory = AnsibleInventory()
    r.status, r.data = "OK", {"hosts": inventory.hosts}
    return r


def get_host_membership(host_name):
    r = APIResponse()
    inventory = AnsibleInventory()
    hosts_groups = inventory.host_show(host_name)
    status_text = "OK" if hosts_groups else "NOTFOUND"

    r.status, r.data = status_text, {"groups": hosts_groups}
    return r
