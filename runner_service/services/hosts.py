import os

from runner_service import AnsibleInventory, configuration
from .utils import APIResponse, fread
from ..utils import ssh_connect_ok

import logging
logger = logging.getLogger(__name__)


def add_host(host_name, group_name):
    r = APIResponse()
    inventory = AnsibleInventory(excl=True)
    if not inventory.loaded:
        r.status, r.msg = "LOCKED", "Unable to lock the inventory file, try later"
        return r

    if group_name not in inventory.groups:
        # invalid request no such group
        r.status, r.msg = "INVALID", "No such group found in the inventory"
        inventory.unlock()
        return r

    group_members = inventory.group_show(group_name)
    if host_name in group_members:
        # host already in that group!
        r.status, r.msg = "OK", "Host already in the group {}".format(group_name)
        inventory.unlock()
        return r

    # At this point, the group is valid, and the host requested isn't already
    # in it, so proceed

    # TODO is name an IP - if so is it valid?
    # TODO if it's a name, does it resolve with DNS?
    if not ssh_connect_ok(host_name):
        pub_key_file = os.path.join(configuration.settings.playbooks_root_dir,
                                    "env/ssh_key.pub")

        r.status, r.msg = "NOAUTH", "SSH connection failed - public key " \
                          "missing on {}? Use the key below".format(host_name)
        r.data = {"pub_key": fread(pub_key_file)}
        inventory.unlock()
        return r

    inventory.host_add(group_name, host_name)
    r.status = "OK"

    return r


def remove_host(host_name, group_name):
    r = APIResponse()
    inventory = AnsibleInventory(excl=True)

    if not inventory.loaded:
        r.status, r.msg = "LOCKED", "Unable to lock the inventory file, try later"
        return r

    if group_name not in inventory.groups or \
      host_name not in inventory.group_show(group_name):
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
