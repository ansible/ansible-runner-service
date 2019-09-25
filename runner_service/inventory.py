
import os
import yaml
import fcntl
import time

from .utils import fread

from runner_service import configuration

import logging
logger = logging.getLogger(__name__)


# By default None is represented in YAML as a 'null' string, so we override
# the representer for NONE type vars with a '' to make the config file more
# human readable
def represent_null(self, _):
    return self.represent_scalar('tag:yaml.org,2002:null', '')


# Add our representer
yaml.add_representer(type(None), represent_null)


class InventoryGroupExists(Exception):
    pass


class InventoryGroupMissing(Exception):
    pass


class InventoryHostMissing(Exception):
    pass


class InventoryRequestInvalid(Exception):
    pass


class InventoryGroupEmpty(Exception):
    pass


class InventoryWriteError(Exception):
    pass


class InventoryreadError(Exception):
    pass


class InventoryCorruptError(Exception):
    pass


class InventoryOperationNotAllowed(Exception):
    pass


def no_group(func):
    def func_wrapper(*args):
        obj, group = args
        if group in obj.groups:
            logger.debug("Group add request for '{}' failed - it already "
                         "exists".format(group))
            if obj.exclusive_lock:
                obj.unlock()
            raise InventoryGroupExists("Group {} already exists".format(group))
        else:
            return func(*args)
    return func_wrapper


def group_exists(func):
    def func_wrapper(*args):
        obj, group = args[:2]
        if group not in obj.groups:
            logger.debug("Group request for '{}' failed - it's not in "
                         "the inventory".format(group))
            if obj.exclusive_lock:
                obj.unlock()
            raise InventoryGroupMissing("{} not in Inventory".format(group))
        else:
            return func(*args)
    return func_wrapper


def host_exists(func):
    def func_wrapper(*args):
        obj, group, host = args[:3]
        if host not in obj.group_show(group):
            logger.debug("request for '{}' failed - it's not in "
                         "the inventory".format(host))
            if obj.exclusive_lock:
                obj.unlock()
            raise InventoryHostMissing("{} not in group '{}'".format(host,
                                                                     group))
        else:
            return func(*args)
    return func_wrapper


class AnsibleInventory(object):
    inventory_seed = {"all": {"children": None}}

    def __init__(self, inventory_file=None, excl=False):

        if not inventory_file:
            self.filename = os.path.join(configuration.settings.playbooks_root_dir,     # noqa
                                         "inventory",
                                         "hosts")
        else:
            self.filename = os.path.expanduser(inventory_file)

        self.inventory = None
        self.exclusive_lock = excl
        self.fd = None
        self.load()

    def __del__(self):
        """ The destructor is needed because we keep a file descriptor open
        if we work in exclusive mode and we do not execute a write op.
        """
        if self.exclusive_lock:
            self.fd.close()

    def load(self):

        if not os.path.exists(self.filename):

            try:
                # could use Python 3 exclusive creation open(file, 'x'), but..
                self.fd = open(self.filename, 'w')
                fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError as _e:
                logger.warning("Race condition hit creating Inventory "
                               "file: {}".format(_e))
            else:
                try:
                    self.fd.write(yaml.safe_dump(AnsibleInventory.inventory_seed,   # noqa
                                                 default_flow_style=False))
                    fcntl.flock(self.fd, fcntl.LOCK_UN)
                except IOError as _e:
                    raise InventoryWriteError("Seeding inventory failed: {}".format(_e))    # noqa
            finally:
                self.fd.close()

        try:
            if self.exclusive_lock:
                locked = False
                self.fd = open(self.filename, 'r+')
                num_retries = 5
                for _d in range(num_retries):
                    try:
                        self.lock()
                    except IOError as _e:
                        # Can't obtain an exclusive_lock
                        logger.warning("Unable to lock inventory (attempt "
                                       "{}/{}): {}".format(_d + 1,
                                                           num_retries,
                                                           _e))
                        time.sleep(.05)     # wait 50ms before retry
                    else:
                        locked = True
                        raw = self.fd.read().strip()
                        break

                if not locked:
                    self.fd.close()
                    return
            else:
                raw = fread(self.filename)
        except Exception as ex:
            raise InventoryreadError("Unable to read the inventory file at "
                                     "{}, error: {}".format(self.filename, ex))

        if not raw:
            # If the inventory is empty for some extrange reason
            self.inventory = None
        else:
            # invalid yaml management
            try:
                self.inventory = yaml.safe_load(raw)
            except yaml.YAMLError as ex:
                raise \
                    InventoryCorruptError("Unable to understand the inventory"
                                          " yaml file at {}, error: "
                                          "{}".format(self.filename, ex))

    def _dump(self):
        return yaml.safe_dump(self.inventory, default_flow_style=False)

    def save(self):
        # Changes in inventory only allowed with exclusive lock
        if not self.exclusive_lock:
            raise \
                InventoryOperationNotAllowed("Internal issue: Inventory "
                                             "modification not allowed")

        self.fd.seek(0)
        self.fd.write(self._dump())
        self.fd.truncate()
        self.unlock()

    def lock(self):
        fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def unlock(self):
        fcntl.flock(self.fd, fcntl.LOCK_UN)
        self.fd.close()

    def __str__(self):
        return self._dump()

    @property
    def loaded(self):
        return self.inventory is not None

    @property
    def hosts(self):
        _host_list = set()
        for group_name in self.groups:
            try:
                _host_list.update(list(self.inventory['all']['children'][group_name]['hosts'].keys())) # noqa
            except (AttributeError, TypeError):
                # group is empty
                pass
        return sorted(list(_host_list))

    @property
    def groups(self):
        try:
            return list(self.inventory['all']['children'].keys())
        except (AttributeError, TypeError):
            return []

    @no_group
    def group_add(self, group):
        node = self.inventory['all']['children']
        if not isinstance(node, dict):
            self.inventory['all']['children'] = dict()
        self.inventory['all']['children'][group] = {"hosts": None}
        logger.info("Group '{}' added to the inventory".format(group))
        self.save()

    @group_exists
    def group_remove(self, group):
        del self.inventory['all']['children'][group]
        logger.info("Group '{}' removed from the inventory".format(group))
        if not self.inventory['all']['children']:
            self.inventory['all']['children'] = None
        self.save()

    @group_exists
    def group_show(self, group):
        if isinstance(self.inventory['all']['children'][group], dict):
            if isinstance(self.inventory['all']['children'][group]['hosts'], dict):     # noqa
                return list(self.inventory['all']['children'][group]['hosts'].keys())   # noqa
            else:
                return []
        else:
            return []

    @group_exists
    def host_add(self, group, host, port=None):
        node = self.inventory['all']['children'][group]['hosts']
        if not isinstance(node, dict):
            self.inventory['all']['children'][group]['hosts'] = {}
        self.inventory['all']['children'][group]['hosts'][host] = None
        if port:
            self.inventory['all']['children'][group]['hosts'][host] = {
                'ansible_host': host,
                'ansible_port': port,
            }
        logger.info("Host '{}' added to the inventory group "
                    "'{}'".format(host, group))
        self.save()

    @group_exists
    def host_remove(self, group, host):
        node = self.inventory['all']['children'][group]['hosts']
        if isinstance(node, dict):
            if host not in self.inventory['all']['children'][group]['hosts']:
                raise InventoryHostMissing("Host {} not in {}".format(host,
                                                                      group))
            else:
                del self.inventory['all']['children'][group]['hosts'][host]
                logger.info("Host '{}' removed from inventory group "
                            "'{}'".format(host, group))
                if not self.inventory['all']['children'][group]['hosts']:
                    self.inventory['all']['children'][group]['hosts'] = None
                self.save()
        else:
            logger.debug("Host removal attempted against the empty "
                         "group '{}'".format(group))
            raise InventoryGroupEmpty("Group is empty")

    def host_show(self, host):
        host_groups = list()
        for group in self.groups:
            if host in self.group_show(group):
                host_groups.append(group)

        return host_groups

    @group_exists
    @host_exists
    def host_vars_add(self, group, host, vars):
        if isinstance(vars, dict):
            self.inventory['all']['children'][group]['hosts'][host] = vars
            self.save()
        else:
            self.unlock()
            logger.error("Invalid request to add vars to a host. "
                         "Vars were:".format(vars))
            raise InventoryRequestInvalid("VARS must be a dict object")

    @group_exists
    @host_exists
    def host_vars_remove(self, group, host):
        self.inventory['all']['children'][group]['hosts'][host] = None
        self.save()

    @group_exists
    @host_exists
    def host_vars_show(self, group, host):
        if self.inventory['all']['children'][group]['hosts'][host]:
            return self.inventory['all']['children'][group]['hosts'][host]
        else:
            return {}

    @group_exists
    def group_vars_show(self, group):
        if 'vars' in self.inventory['all']['children'][group]:
            return self.inventory['all']['children'][group]['vars']
        else:
            return {}

    @group_exists
    def group_vars_add(self, group, vars):
        if isinstance(vars, dict):
            self.inventory['all']['children'][group]['vars'] = vars
            self.save()
        else:
            self.unlock()
            logger.error("Invalid request to add vars to a group. "
                         "Vars were:".format(vars))
            raise InventoryRequestInvalid("VARS must be a dict object")

    @group_exists
    def group_vars_remove(self, group):
        if 'vars' in self.inventory['all']['children'][group]:
            del self.inventory['all']['children'][group]['vars']
            self.save()
        else:
            self.unlock()
            logger.error("Request to delete group vars that didn't exist")
