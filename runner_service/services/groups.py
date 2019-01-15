
from runner_service import (AnsibleInventory,
                            InventoryGroupExists,
                            InventoryGroupMissing
                            )
from .utils import APIResponse

import logging
logger = logging.getLogger(__name__)


def add_group(group_name):
    r = APIResponse()

    reserved_group_names = ['all']
    if group_name in reserved_group_names:
        r.status, r.msg = "INVALID", \
                          "Group name '{}' is a reserved/system group " \
                          "name".format(group_name)
        return r

    inventory = AnsibleInventory(excl=True)
    if inventory.loaded:
        try:
            inventory.group_add(group_name)
        except InventoryGroupExists:
            r.status, r.msg = 'OK', 'Group already exists'
        else:
            r.status, r.msg = 'OK', 'Group {} added'.format(group_name)

        return r
    else:
        r.status, r.msg = 'LOCKED', 'Unable to lock the inventory file'
        return r


def remove_group(group_name):
    r = APIResponse()
    inventory = AnsibleInventory(excl=True)
    if inventory.loaded:
        try:
            inventory.group_remove(group_name)
        except InventoryGroupMissing:
            r.status, r.msg = 'INVALID', "Group doesn't exist"
        else:
            r.status, r.msg = 'OK', 'Group {} removed'.format(group_name)

        return r
    else:
        r.status, r.msg = 'LOCKED', 'Unable to lock the inventory file'
        return r


def get_groups():
    r = APIResponse()
    inventory = AnsibleInventory()
    r.status, r.data = 'OK', {"groups": inventory.groups}
    return r


def get_group_members(group_name):
    r = APIResponse()
    inventory = AnsibleInventory()
    try:
        group_hosts = inventory.group_show(group_name)
    except InventoryGroupMissing:
        r.status, r.msg = 'NOTFOUND', "Group doesn't exist"
    else:
        r.status, r.data = "OK", {"members": group_hosts}
    return r
