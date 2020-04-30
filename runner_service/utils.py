import os
import shlex
import shutil
import socket
import sys
import getpass

from subprocess import Popen, PIPE
from threading import Timer

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from OpenSSL import crypto


from runner_service import configuration

import logging
logger = logging.getLogger(__name__)


class RunnerServiceError(Exception):
    pass

def create_directory(dir_path):
    """ Create directory if it doesn't exist """
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

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

        # create cert_dir if it doesn't exist
        create_directory(cert_dir)

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

    prv_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend())
    pub_key = prv_key.public_key()

    prv_file = os.path.join(ssh_dir, 'ssh_key')
    pub_file = os.path.join(ssh_dir, 'ssh_key.pub')

    # create ssh_dir if it doesn't exist
    create_directory(ssh_dir)

    # export the private key
    try:
        with open(prv_file, "wb") as f:
            f.write(prv_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption()))

    except (OSError, IOError) as err:
        msg = "Unable to write to private key to '{}': {}".format(ssh_dir, err)
        logger.critical(msg)
        raise RunnerServiceError(msg)
    except Exception as err:
        logger.critical("Unknown error writing private key: {}".format(err))
        raise
    else:
        # python3 syntax
        os.chmod(prv_file, 0o600)
        logger.info("Created SSH private key @ '{}'".format(prv_file))

    # export the public key
    try:
        with open(pub_file, "wb") as f:
            f.write(pub_key.public_bytes(
                    encoding=serialization.Encoding.OpenSSH,
                    format=serialization.PublicFormat.OpenSSH))

    except (OSError, IOError) as err:
        msg = "Unable to write public ssh key to {}: {}".format(ssh_dir, err)
        logger.critical(msg)
        raise RunnerServiceError(msg)
    except Exception as err:
        logger.critical("Unknown error creating the public key "
                        "to {}: {}".format(ssh_dir, err))
        raise
    else:
        # python3 syntax
        os.chmod(pub_file, 0o644)
        logger.info("Created SSH public key @ '{}'".format(pub_file))


if sys.version_info[0] == 2:
    class ConnectionError(OSError):
        pass

    class ConnectionRefusedError(ConnectionError):
        pass


class HostNotFound(Exception):
    pass


class SSHNotAccessible(Exception):
    pass


class SSHTimeout(Exception):
    pass


class SSHIdentityFailure(Exception):
    pass


class SSHAuthFailure(Exception):
    pass


class SSHUnknownError(Exception):
    pass


class SSHClient(object):
    def __init__(self, user, host, identity, timeout=1, port=22):
        self.user = user
        self.port = port
        self.host = host
        self.timeout = timeout
        self.identity_file = identity

    def connect(self):

        def timeout_handler():
            proc.kill()
            raise SSHTimeout

        socket.setdefaulttimeout(self.timeout)
        try:
            family, *_, sockaddr = socket.getaddrinfo(self.host, self.port, 0, socket.SOCK_STREAM, socket.SOL_TCP)[0]
        except socket.gaierror:
            raise HostNotFound

        with socket.socket(family, socket.SOCK_STREAM, socket.SOL_TCP) as s:
            try:
                s.connect(sockaddr)
            except ConnectionRefusedError:
                raise SSHNotAccessible
            except socket.timeout:
                raise SSHTimeout
            else:
                s.shutdown(socket.SHUT_RDWR)

        # Now try and use the identity file to passwordless ssh
        cmd = ('ssh -o "StrictHostKeyChecking=no" '
               '-o "IdentitiesOnly=yes" '
               ' -o "PasswordAuthentication=no" '
               ' -i {} '
               '{}@{} python --version'.format(self.identity_file, self.user, self.host))

        proc = Popen(shlex.split(cmd), stdout=PIPE, stderr=PIPE)
        timer = Timer(self.timeout, timeout_handler)
        try:
            timer.start()
            stdout, stderr = proc.communicate()
        except Exception as e:
            raise SSHUnknownError(e)
        else:
            if 'permission denied' in stderr.decode().lower():
                raise SSHAuthFailure(stderr)
        finally:
            timer.cancel()


def ssh_connect_ok(host, user=None, port=None):

    if not user:
        if configuration.settings.target_user:
            user = configuration.settings.target_user
        else:
            user = getpass.getuser()

    priv_key = os.path.join(configuration.settings.ssh_private_key)

    if not os.path.exists(priv_key):
        return False, "FAILED:SSH key(s) missing from ansible-runner-service"

    target = SSHClient(
        user=user,
        host=host,
        identity=priv_key,
        timeout=configuration.settings.ssh_timeout,
        port=22 if port is None else port,
    )

    try:
        target.connect()
    except HostNotFound:
        return False, "NOCONN:SSH error - '{}' not found; check DNS or " \
                "/etc/hosts".format(host)
    except SSHNotAccessible:
        return False, "NOCONN:SSH target '{}' not contactable; host offline" \
                      ", port 22 blocked, sshd running?".format(host)
    except SSHTimeout:
        return False, "TIMEOUT:SSH timeout waiting for response from " \
                      "'{}'".format(host)
    except SSHAuthFailure:
        return False, "NOAUTH:SSH auth error - passwordless ssh not " \
            "configured for '{}'".format(host)
    else:
        return True, "OK:SSH connection check to {} successful".format(host)
