import os
import sys
import yaml
import logging


def init(mode='dev'):
    global settings

    settings = Config(mode)


class Config(object):

    MODES = {
        "prod": {
            "logging_conf": "/etc/ansible-runner-service/logging.yaml",
            "log_path": "/var/log",
            "config_file": "/etc/ansible-runner-service/config.yaml",
            "playbooks_root_dir": "/usr/share/ansible-runner-service",
            "templates_dir": "/var/"
        },
        "dev": {
            "logging_conf": "./logging.yaml",
            "log_path": "./",
            "config_file": "./config.yaml",
            "playbooks_root_dir": "./samples"
        }
    }

    def __init__(self, mode='dev'):

        self.mode = mode
        # defaults
        self.playbooks_root_dir = Config.MODES[mode].get('playbooks_root_dir')
        self.logging_conf = Config.MODES[mode].get('logging_conf', None)
        self.log_path = Config.MODES[mode].get('log_path', None)
        self.config_file = Config.MODES[mode].get('config_file', None)
        self.config_dir = os.path.dirname(self.config_file)
        self.passwords = {"admin": "admin"}

        # expiration period in years for the self-signed cert that we generate
        self.cert_expiration = 3

        # ssh connection timeout
        self.ssh_timeout = 2

        # event_threads controls how many event files are scanned concurrently
        self.event_threads = 10

        self.port = 5001
        self.ip_address = '0.0.0.0'
        self.loglevel = logging.DEBUG

        # flask config setting to hide the "production use" warning
        self.ENV = ''

        if os.path.exists(self.config_file):
            self._apply_local()

    def _apply_local(self):

        # apply overrides from configuration settings in /etc/?
        print("Analysing local configuration options from "
              "{}".format(self.config_file))

        try:
            local_config = yaml.load(open(self.config_file, 'r'))
        except yaml.YAMLError as exc:
            print("ERROR: YAML error in configuration file: {}".format(exc))
            sys.exit(12)

        overridden_options = False
        # apply overrides
        for varname in local_config.keys():
            if varname in self.__dict__.keys():
                _value = local_config.get(varname)
                print("- setting {} to {}".format(varname,
                                                  _value))
                setattr(self, varname, _value)
                overridden_options = True

        if not overridden_options:
            print("No configuration settings overridden")
