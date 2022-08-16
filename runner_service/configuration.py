import os
import sys
import yaml
import getpass
import logging
import logging.config

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
out = logging.StreamHandler(sys.stdout)
logger.addHandler(out)


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
            "templates_dir": "/var/",
            "debug": False
        },
        "dev": {
            "logging_conf": os.path.abspath("./logging.yaml"),
            "log_path": os.path.abspath("./"),
            "config_file": os.path.abspath("./config.yaml"),
            "playbooks_root_dir": os.path.abspath("./samples"),
            "debug": True
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
        self.event_cache_size = 3
        self.runner_cache_size = 5
        self.debug = Config.MODES[mode].get("debug", True)

        # Path to custom ssh key, by default project/env/ssh_key is used
        self.ssh_private_key = os.path.join(
            self.playbooks_root_dir,
            "env/ssh_key"
        )

        # maximum age of an artifact folder in days
        # set to 0 to disable the automatic removal of old artifact folders
        self.artifacts_remove_age = 7

        # how frequently the old artifacts should be removed in days
        self.artifacts_remove_frequency = 1

        # expiration period in years for the self-signed cert that we generate
        self.cert_expiration = 3

        # ssh connection timeout
        self.ssh_timeout = 2

        # event_threads controls how many event files are scanned concurrently
        self.event_threads = 10

        self.port = 5001
        self.ip_address = '0.0.0.0'
        self.loglevel = logging.DEBUG

        # provide the ability to skip ssh checks - useful for Travis CI!
        self.ssh_checks = True

        # target user that the service will use for ssh connection
        self.target_user = getpass.getuser()

        # flask config setting to hide the "production use" warning
        self.ENV = ''

        self._apply_overrides()

    def _apply_local(self):
        # apply logging configurations
        if os.path.isfile(self.logging_conf):
            try:
                with open(self.logging_conf, "r") as _cfg:
                    local_config = yaml.safe_load(_cfg.read())
                    logging.config.dictConfig(local_config)
                    global logger
                    logger = logging.getLogger()
            except yaml.YAMLError as exc:
                logger.error("ERROR: YAML error in logging configuration "
                             "file: {}".format(exc))

        # apply overrides from configuration settings in /etc/?
        logger.info("Analysing local configuration options from "
                    "{}".format(self.config_file))

        try:
            with open(self.config_file, "r") as _cfg:
                local_config = yaml.load(_cfg.read(), Loader=yaml.SafeLoader)
        except yaml.YAMLError as exc:
            logger.critical("ERROR: YAML error in configuration "
                            "file: {}".format(exc))
            sys.exit(12)

        overridden_options = False
        # apply overrides from
        for varname in local_config.keys():
            if varname in self.__dict__.keys():
                _value = local_config.get(varname)
                logger.info("- setting {} to {}".format(varname,
                                                        _value))
                setattr(self, varname, _value)
                overridden_options = True

        if not overridden_options:
            logger.info("No configuration settings overridden")

    def _apply_runtime(self):

        logger.info("Analysing runtime overrides from environment variables")

        overridden_options = False

        for varname in os.environ.keys():
            if varname in self.__dict__.keys():
                _value = self._convert_value(os.environ[varname])
                logger.info("- setting {} to {}".format(varname, _value))
                setattr(self, varname, _value)
                overridden_options = True

        if not overridden_options:
            logger.info("No configuration settings overridden")

    def _convert_value(self, value):
        bool_types = {
            "TRUE": True,
            "FALSE": False,
        }

        if value.isdigit():
            value = int(value)
        elif value.upper() in bool_types:
            value = bool_types[value.upper()]

        return value

    def _apply_overrides(self):

        if os.path.exists(self.config_file):
            self._apply_local()

        self._apply_runtime()
