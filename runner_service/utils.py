import os
import yaml
import time
import shutil
import threading

from socket import gethostname
from OpenSSL import crypto

from runner_service import configuration

import logging
logger = logging.getLogger(__name__)


# Ny default None is represented in YAML as a 'null' string, so we override
# the representer for NONE type vars with a '' to make the config file more
# human readable
def represent_null(self, _):
    return self.represent_scalar('tag:yaml.org,2002:null', '')


# Add our representer
yaml.add_representer(type(None), represent_null)


class RunnerServiceError(Exception):
    pass


def fread(file_path):
    """ return the contents of the given file """
    with open(file_path, 'r') as file_fd:
        return file_fd.read().strip()


def create_self_signed_cert(cert_dir, cert_pfx):
    """
    Looks in cert_dir for the key files (using the cert_pfx name), and either
    returns if they exist, or create them if they're missing.
    """

    cert_filename = os.path.join(cert_dir,
                                 "{}.crt".format(cert_pfx))
    key_filename = os.path.join(cert_dir,
                                "{}.key".format(cert_pfx))

    logger.debug("Checking for the SSL keys in {}".format(cert_dir))
    if os.path.exists(cert_filename) \
            or os.path.exists(key_filename):
        logger.info("Using existing SSL files in {}".format(cert_dir))
        return (cert_filename, key_filename)
    else:
        logger.info("Existing SSL files not found in {}".format(cert_dir))
        logger.info("Self-signed cert will be created - expiring in {} "
                    "years".format(configuration.settings.cert_expiration))

        # create a key pair
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 1024)

        # create a self-signed cert
        cert = crypto.X509()
        cert.get_subject().C = "US"
        cert.get_subject().ST = "North Carolina"
        cert.get_subject().L = "Raliegh"
        cert.get_subject().O = "Red Hat"
        cert.get_subject().OU = "Ansible"
        cert.get_subject().CN = gethostname()
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)

        # define cert expiration period(years)
        cert.gmtime_adj_notAfter(configuration.settings.cert_expiration * 365 * 24 * 60 * 60)

        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(k)
        cert.sign(k, 'sha512')

        logger.debug("Writing crt file to {}".format(cert_filename))
        with open(os.path.join(cert_dir, cert_filename), "wt") as cert_fd:
            cert_fd.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode('utf-8'))

        logger.debug("Writing key file to {}".format(key_filename))
        with open(os.path.join(cert_dir, key_filename), "wt") as key_fd:
            key_fd.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k).decode('utf-8'))

        return (cert_filename, key_filename)


class TimeOutLock(object):

    cond = threading.Condition(threading.Lock())

    def __init__(self, lock_object):
        self.mutex = lock_object

    def wait(self, timeout_secs):
        with TimeOutLock.cond:
            current_time = start_time = time.time()
            while current_time < start_time + timeout_secs:
                # try and acquire the lock, but don't block
                if self.mutex.acquire(False):
                    # got it!
                    return True
                else:
                    TimeOutLock.cond.wait(timeout_secs - current_time + start_time)
                    current_time = time.time()

        # timeout hit, couldn't acquire the lock in time
        return False

    def reset(self):
        self.mutex.release()
        try:
            TimeOutLock.cond.notify()
        except RuntimeError:
            # cond is not held by anyone
            pass


def rm_r(path):
    if not os.path.exists(path):
        return
    if os.path.isfile(path) or os.path.islink(path):
        os.unlink(path)
    else:
        shutil.rmtree(path)


class InventoryGroupExists(Exception):
    pass


class InventoryGroupMissing(Exception):
    pass


class InventoryHostMissing(Exception):
    pass


class InventoryGroupEmpty(Exception):
    pass


class InventoryWriteError(Exception):
    pass


def no_group(func):
    def func_wrapper(*args):
        obj, group = args
        if group in obj.sections:
            logger.debug("Group add request for '{}' failed - it already "
                         "exists".format(group))
            raise InventoryGroupExists("Group {} already exists".format(group))
        else:
            return func(*args)
    return func_wrapper


def group_exists(func):
    def func_wrapper(*args):
        obj, group, *rest = args
        if group not in obj.sections:
            logger.debug("Group request for '{}' failed - it's not in "
                         "the inventory".format(group))
            raise InventoryGroupMissing("{} not found in the Inventory".format(group))
        else:
            return func(*args)
    return func_wrapper


class AnsibleInventory(object):
    inventory_seed = {"all": {"children": None, "hosts": None}}

    def __init__(self, inventory_file=None):

        if not inventory_file:
            self.filename = os.path.join(configuration.settings.playbooks_root_dir,
                                         "inventory",
                                         "hosts")
        else:
            self.filename = os.path.expanduser(inventory_file)

        self.inventory = None

        self.load()

    def load(self):

        if not os.path.exists(self.filename):
            try:
                with open(self.filename, 'w') as inv:
                    inv.write(yaml.dump(AnsibleInventory.inventory_seed,
                                        default_flow_style=False))
            except IOError:
                raise InventoryWriteError("Unable to create the seed inventory"
                                          " file at {}".format(self.filename))

        raw = fread(self.filename)

        if not raw:
            self.inventory = None
        else:
            self.inventory = yaml.safe_load(raw)

    def _dump(self):
        return yaml.dump(self.inventory, default_flow_style=False)

    def write(self):
        with open(self.filename, 'w') as fd:
            fd.write(self._dump())

    def __str__(self):
        return self._dump()

    @property
    def sections(self):
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

    @group_exists
    def group_remove(self, group):
        del self.inventory['all']['children'][group]
        logger.info("Group '{}' removed from the inventory".format(group))
        if not self.inventory['all']['children']:
            self.inventory['all']['children'] = None

    @group_exists
    def group_show(self, group):
        if isinstance(self.inventory['all']['children'][group], dict):
            if isinstance(self.inventory['all']['children'][group]['hosts'], list):
                return self.inventory['all']['children'][group]['hosts']
            else:
                return []
        else:
            return []

    @group_exists
    def host_add(self, group, host):
        node = self.inventory['all']['children'][group]['hosts']
        if not isinstance(node, list):
            self.inventory['all']['children'][group]['hosts'] = []
        self.inventory['all']['children'][group]['hosts'].append(host)
        logger.info("Host '{}' added to the inventory group "
                    "'{}'".format(host, group))

    @group_exists
    def host_remove(self, group, host):
        node = self.inventory['all']['children'][group]['hosts']
        if isinstance(node, list):
            if host not in self.inventory['all']['children'][group]['hosts']:
                raise InventoryHostMissing("Host {} not in {}".format(host,
                                                                      group))
            else:
                self.inventory['all']['children'][group]['hosts'].remove(host)
                logger.info("Host ''{}' removed from inventory group "
                            "'{}'".format(host, group))
                if not self.inventory['all']['children'][group]['hosts']:
                    self.inventory['all']['children'][group]['hosts'] = None
        else:
            logger.debug("Host removal attempted against the empty "
                         "group '{}'".format(group))
            raise InventoryGroupEmpty("Group is empty")
