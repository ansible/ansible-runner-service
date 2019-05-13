import os
import shutil
import socket
import getpass

from OpenSSL import crypto
from paramiko.rsakey import RSAKey
from paramiko import SSHClient, AutoAddPolicy
from paramiko.ssh_exception import (AuthenticationException,
                                    NoValidConnectionsError,
                                    SSHException)

from runner_service import configuration

import logging
logger = logging.getLogger(__name__)


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
        k.generate_key(crypto.TYPE_RSA, 2048)

        # create a self-signed cert
        cert = crypto.X509()
        cert.get_subject().C = "US"
        cert.get_subject().ST = "North Carolina"
        cert.get_subject().L = "Raliegh"
        cert.get_subject().O = "Red Hat"         # noqa: E741
        cert.get_subject().OU = "Ansible"
        cert.get_subject().CN = socket.gethostname()
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)

        # define cert expiration period(years)
        cert.gmtime_adj_notAfter(configuration.settings.cert_expiration * 365 * 24 * 60 * 60)   # noqa

        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(k)
        cert.sign(k, 'sha512')

        logger.debug("Writing crt file to {}".format(cert_filename))
        with open(os.path.join(cert_dir, cert_filename), "wt") as cert_fd:
            cert_fd.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode('utf-8'))   # noqa

        logger.debug("Writing key file to {}".format(key_filename))
        with open(os.path.join(cert_dir, key_filename), "wt") as key_fd:
            key_fd.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k).decode('utf-8'))    # noqa

        return (cert_filename, key_filename)


def rm_r(path):
    if not os.path.exists(path):
        return
    if os.path.isfile(path) or os.path.islink(path):
        os.unlink(path)
    else:
        shutil.rmtree(path)


def ssh_create_key(ssh_dir, user=None):

    if not user:
        user = getpass.getuser()

    key = RSAKey.generate(4096)
    pub_file = os.path.join(ssh_dir, 'ssh_key.pub')
    prv_file = os.path.join(ssh_dir, 'ssh_key')
    comment_str = '{}@{}'.format(user, socket.gethostname())

    # Setup the public key file
    try:
        with open(pub_file, "w") as pub:
            pub.write("ssh-rsa {} {}\n".format(key.get_base64(),
                                               comment_str))
    except (PermissionError, IOError) as err:
        msg = "Unable to write public ssh key to {}: {}".format(ssh_dir, err)
        logger.critical(msg)
        raise RunnerServiceError(msg)
    except Exception as err:
        logger.critical("Unknown error creating the public key "
                        "to {}: {}".format(ssh_dir, err))
        raise
    else:
        # python3 syntax
        os.chmod(pub_file, 0o600)
        logger.info("Created SSH public key @ '{}'".format(pub_file))

    # setup the private key file
    try:
        with open(prv_file, "w") as prv:
            key.write_private_key(prv)
    except (PermissionError, IOError) as err:
        msg = "Unable to write to private key to '{}': {}".format(ssh_dir, err)
        logger.critical(msg)
        raise RunnerServiceError(msg)
    except SSHException as err:
        msg = "SSH key generated is invalid: {}".format(err)
        logger.critical(msg)
        raise RunnerServiceError(msg)
    except Exception as err:
        logger.critical("Unknown error writing private key: {}".format(err))
        raise
    else:
        # python3 syntax
        os.chmod(prv_file, 0o600)
        logger.info("Created SSH private key @ '{}'".format(prv_file))


def ssh_connect_ok(host, user=None):

    if not user:
        if configuration.settings.target_user:
            user = configuration.settings.target_user
        else:
            user = getpass.getuser()

    client = SSHClient()
    client.set_missing_host_key_policy(AutoAddPolicy())

    priv_key = os.path.join(configuration.settings.playbooks_root_dir,
                            "env/ssh_key")

    if not os.path.exists(priv_key):
        return False, "FAILED:SSH key(s) missing from ansible-runner-service"

    conn_args = {
        "hostname": host,
        "username": user,
        "timeout": configuration.settings.ssh_timeout,
        "key_filename": [priv_key]
    }

    try:
        client.connect(**conn_args)

    except socket.timeout:
        return False, "TIMEOUT:SSH timeout waiting for response from " \
                      "'{}'".format(host)

    except (AuthenticationException, SSHException):
        return False, "NOAUTH:SSH auth error - passwordless ssh not " \
                      "configured for '{}'".format(host)

    except NoValidConnectionsError:
        return False, "NOCONN:SSH target '{}' not contactable; host offline" \
                      ", port 22 blocked, sshd running?".format(host)

    except socket.gaierror:
        return False, "NOCONN:SSH error - '{}' not found; check DNS or " \
                      "/etc/hosts".format(host)

    else:
        client.close()
        return True, "OK:SSH connection check to {} successful".format(host)
