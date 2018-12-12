import os

from .utils import APIResponse, loadYAML, writeYAML

from runner_service import (AnsibleInventory,
                            InventoryRequestInvalid,
                            InventoryGroupMissing,
                            InventoryHostMissing
                            )

import runner_service.configuration as configuration

import logging
logger = logging.getLogger(__name__)


def get_hostvars(host_name, group_name):
    r = APIResponse()
    inventory = AnsibleInventory()

    hostvars_path = os.path.join(configuration.settings.playbooks_root_dir,
                                 "project",
                                 "host_vars",
                                 host_name)

    if os.path.exists(hostvars_path):
        logger.debug("HOSTVARs 'get' request serviced from filesystem")
        vars = loadYAML(hostvars_path)
    else:
        # try the inventory - will yield empty if nothing there
        try:
            vars = inventory.host_vars_show(group_name, host_name)
            logger.debug("HOSTVARs get request serviced from the inventory")
        except (InventoryHostMissing, InventoryGroupMissing) as e:
            r.status, r.msg = 'NOTFOUND', \
                              "Host/group not found"
            return r

    r.status, r.data = 'OK', {"vars": vars}
    return r


def add_hostvars(host_name, group_name, vars, store_type='file'):
    r = APIResponse()
    r.data = {"hostname": host_name}

    if store_type == 'file':
        # create the pathname and ensure the subdirs exist
        hostvars_dir = os.path.join(configuration.settings.playbooks_root_dir, # noqa
                                    "project", "host_vars")
        if not os.path.exists(hostvars_dir):
            try:
                os.makedirs(hostvars_dir)
            except OSError as e:
                # directory exists - race condition hit, ignore it
                logger.debug("Hit race condition for hostvars dir create: {}".format(e)) # noqa
                if e.errno != 17:
                    raise

        hostvars_file = os.path.join(hostvars_dir, host_name)
        if writeYAML(vars, hostvars_file):
            r.status, r.msg = "OK", \
                              "Variables written successfully to " \
                              "{}".format(hostvars_file)
            return r
        else:
            r.status, r.msg = "FAILED", \
                              "Unable to write variables to the " \
                              "filesystem @ {}".format(hostvars_file)
            return r
    else:
        # Store the variables directly in the inventory
        inventory = AnsibleInventory(excl=True)
        if not inventory.loaded:
            r.status, r.msg = "LOCKED", \
                              "Unable to lock the inventory file, try later"
            return r

        # if host_name not in inventory.group_show(group_name):
        #     r.status, r.msg = "NOTFOUND", \
        #                       "Host '{}' not in group '{}'".format(host_name,
        #                                                            group_name)
        #     return r

        try:
            inventory.host_vars_add(group_name, host_name, vars)

        except InventoryHostMissing as e:
            r.status, r.msg = "NOTFOUND", \
                              "Requested host not found ({})".format(e)
            return r
        except InventoryGroupMissing as e:
            r.status, r.msg = "NOTFOUND", \
                              "Requested group not found ({})".format(e)
            return r
        except InventoryRequestInvalid as e:
            r.status, r.msg = "INVALID", \
                              "Vars must be a JSON object ({})".format(e)
            return r

    r.status, r.msg = "OK", \
                      "Vars added to {}".format(host_name)
    return r


def remove_hostvars(host_name, group_name):
    r = APIResponse()
    r.data = {"hostname": host_name}

    hostvars_path = os.path.join(configuration.settings.playbooks_root_dir,
                                 "project",
                                 "host_vars",
                                 host_name)

    logger.debug("Deleting HOSTVARs for {} from filesystem".format(host_name))
    try:
        os.remove(hostvars_path)
    except OSError as e:
        if e.errno == 2:
            # file doesn't exist, ignore the error
            pass
        else:
            raise

    # now remove from the inventory
    inventory = AnsibleInventory(excl=True)
    if not inventory.loaded:
        r.status, r.msg = "LOCKED", \
                          "Unable to lock the inventory file, try later"
        return r

    if host_name not in inventory.group_show(group_name):
        r.status, r.msg = "NOTFOUND", \
                          "Host '{}' not in group '{}'".format(host_name,
                                                               group_name)
        return r

    try:
        inventory.host_vars_remove(group_name, host_name)

    except InventoryHostMissing as e:
        r.status, r.msg = "NOTFOUND", \
                          "Host '{}' not in group '{}'".format(host_name,
                                                               group_name)
        return r
    except InventoryGroupMissing as e:
        r.status, r.msg = "NOTFOUND", \
                          "Group '{}' does not exist".format(group_name)
        return r

    r.status, r.msg = "OK", \
                      "Vars removed for '{}' in group '{}'".format(host_name,
                                                                   group_name)
    return r


def get_groupvars(group_name):
    r = APIResponse()
    groupvars_path = os.path.join(configuration.settings.playbooks_root_dir,
                                  "project",
                                  "group_vars",
                                  "{}.yml".format(group_name))

    if os.path.exists(groupvars_path):
        logger.debug("GROUPVARs GET request serviced from filesystem")
        vars = loadYAML(groupvars_path)
    else:
        # group_vars not in the filesystem, so look at the Inventory
        inventory = AnsibleInventory()
        try:
            vars = inventory.group_vars_show(group_name)
            logger.debug("GROUPVARs get request serviced from the inventory")
        except (InventoryGroupMissing) as e:
            r.status, r.msg = 'NOTFOUND', \
                              "group not found"
            return r

    r.status, r.data = 'OK', {"vars": vars}
    return r


def add_groupvars(group_name, vars, store_type='file'):
    r = APIResponse()

    if store_type == 'file':
        logger.debug("Processing groupvars request for the filesystem")
        # create the pathname and ensure the subdirs exist
        groupvars_dir = os.path.join(configuration.settings.playbooks_root_dir, # noqa
                                    "project", "group_vars")
        if not os.path.exists(groupvars_dir):
            try:
                os.makedirs(groupvars_dir)
            except OSError as e:
                # directory exists - race condition hit, ignore it
                logger.debug("Hit race condition for groupvars dir create: {}".format(e)) # noqa
                if e.errno != 17:
                    raise

        groupvars_path = os.path.join(groupvars_dir,
                                      "{}.yml".format(group_name))

        if writeYAML(vars, groupvars_path):
            r.status, r.msg = "OK", \
                              "Variables written successfully to " \
                              "{}".format(groupvars_path)
            return r
        else:
            r.status, r.msg = "FAILED", \
                              "Unable to write variables to the " \
                              "filesystem @ {}".format(groupvars_path)
            return r
    else:
        # inventory group vars is requested
        # Store the variables directly in the inventory
        inventory = AnsibleInventory(excl=True)
        if not inventory.loaded:
            r.status, r.msg = "LOCKED", \
                              "Unable to lock the inventory file, try later"
            return r

        if group_name not in inventory.groups:
            r.status, r.msg = "NOTFOUND", \
                              "Group '{}' not in inventory '{}'".format(group_name) # noqa
            return r

        try:
            inventory.group_vars_add(group_name, vars)

        except InventoryRequestInvalid as e:
            r.status, r.msg = "INVALID", \
                              "Vars must be a JSON object ({})".format(e)
            return r
        else:
            r.status, r.msg = "OK", \
                "Vars added to {}".format(group_name)
            return r


def remove_groupvars(group_name):
    r = APIResponse()

    groupvars_path = os.path.join(configuration.settings.playbooks_root_dir,
                                  "project",
                                  "group_vars",
                                  "{}.yml".format(group_name))

    logger.debug("Deleting GROUPVARs for {} from filesystem".format(group_name))    # noqa
    try:
        os.remove(groupvars_path)
    except OSError as e:
        if e.errno == 2:
            # file doesn't exist, ignore the error
            pass
        else:
            raise

    # now remove from the inventory
    inventory = AnsibleInventory(excl=True)
    if not inventory.loaded:
        r.status, r.msg = "LOCKED", \
                          "Unable to lock the inventory file, try later"
        return r

    try:
        inventory.group_vars_remove(group_name)

    except InventoryGroupMissing as e:
        r.status, r.msg = "NOTFOUND", \
                          "Group '{}' does not exist".format(group_name)
        return r
    else:
        r.status, r.msg = "OK", \
                          "group vars removed for '{}'".format(group_name)
        return r
