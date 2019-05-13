#!/usr/bin/env python

# python2 or python3 compatible

import os
import sys
import yaml
import signal
import logging
import logging.config

import runner_service.configuration as configuration
from runner_service.utils import (fread,
                                  create_self_signed_cert,
                                  ssh_create_key,
                                  RunnerServiceError)
from runner_service.app import create_app


def signal_stop(*args):
    '''
    Handle SIGTERM when running in the background
    '''
    print("Shutting ansible-runner-service down - service stopped by admin")
    sys.exit(0)


def get_ssl():
    """
    Ensure the SSL files exist, so flask can run under https
    """
    cert_filename_pfx = os.path.splitext(os.path.basename(__file__))[0]

    return create_self_signed_cert(cert_dir=configuration.settings.config_dir,
                                   cert_pfx=cert_filename_pfx)


def setup_logging():
    """ Setup logging """

    logging_config = configuration.settings.logging_conf
    pfx = configuration.settings.log_path

    if os.path.exists(logging_config):

        try:
            config = yaml.safe_load(fread(logging_config))
        except yaml.YAMLError as _e:
            print("ERROR: logging configuration error: {}".format(_e))
            sys.exit(12)

        fname = config.get('handlers').get('file_handler')['filename']

        full_path = os.path.join(pfx, fname)

        config.get('handlers').get('file_handler')['filename'] = full_path

        logging.config.dictConfig(config)
        logging.info("Loaded logging configuration from "
                     "{}".format(logging_config))
    else:
        logging.basicConfig(level=logging.DEBUG)
        logging.warning("Logging configuration file ({}) not found, using "
                        "basic logging".format(logging_config))


def get_mode():
    """ get the runtime mode """

    # set the mode based on where this is running from
    if os.path.dirname(__file__).startswith("/usr"):
        return 'prod'
    else:
        return 'dev'


def setup_ssh():

    env_dir = os.path.join(configuration.settings.playbooks_root_dir,
                           "env")
    ssh_files = [os.path.join(env_dir, 'ssh_key'),
                 os.path.join(env_dir, 'ssh_key.pub')
                 ]
    ssh_states = [os.path.exists(_f) for _f in ssh_files]

    if all(ssh_states):
        logging.info("SSH keys present in {}".format(env_dir))
        return

    elif all([not state for state in ssh_states]):
        logging.debug("No SSH keys present in {}".format(env_dir))
        logging.info("Creating SSH keys")
        # no keys are setup, so create them
        try:
            ssh_create_key(env_dir)
        except RunnerServiceError:
            logging.critical("Unable to create SSH Keys - service aborted")
            sys.exit(12)
        else:
            return

    elif any(ssh_states):
        # one of the files exists without the other - admin intervention req'd
        logging.critical("The existing pub/priv key pair is incomplete (one"
                         " exists without the other). Service aborting")
        sys.exit(12)


def setup_localhost_ssh():
    ssh_home = os.path.join(os.path.expanduser('~'), '.ssh')
    if not os.path.exists(ssh_home):
        os.mkdir(ssh_home)
        os.chmod(ssh_home, 0o700)
    authorized_keys = os.path.join(ssh_home, "authorized_keys")

    root_dir = configuration.settings.playbooks_root_dir
    app_pub_key = fread(os.path.join(root_dir, "env", "ssh_key.pub"))

    if not os.path.exists(authorized_keys):
        with open(authorized_keys, "w") as auth_file:
            auth_file.write(app_pub_key)
        os.chmod(authorized_keys, 0o644)
    else:
        # it does exist, so see if our key should be appended
        with open(authorized_keys, "r") as auth_file:
            auth_data = auth_file.read().splitlines()
        if app_pub_key not in auth_data:
            with open(authorized_keys, "a") as auth_file:
                auth_file.write("{}\n".format(app_pub_key))
        else:
            pass


def setup_common_environment():

    setup_logging()
    logging.info("Run mode is: {}".format(configuration.settings.mode))

    setup_ssh()

    setup_localhost_ssh()


def main(test_mode=False):

    # Setup log and ssh and other things present in all the environments
    setup_common_environment()

    # setup ssl for the Flask http server
    ssl_context = get_ssl()

    app = create_app()

    if test_mode:
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        return app.test_client()

    # Start the API server
    app.run(host=configuration.settings.ip_address,
            port=configuration.settings.port,
            threaded=True,
            ssl_context=ssl_context,
            debug=configuration.settings.debug,
            use_reloader=False)


if __name__ == "__main__":

    # setup signal handler for a kill/sigterm request (background mode)
    signal.signal(signal.SIGTERM, signal_stop)

    mode = get_mode()

    print("Starting ansible-runner-service")
    configuration.init(mode=mode)

    main()
