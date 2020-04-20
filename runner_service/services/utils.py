import os
import glob
import yaml

import runner_service.configuration as configuration


def playbook_exists(playbook_name):
    playbook_path = os.path.join(configuration.settings.playbooks_root_dir,
                                 "project",
                                 playbook_name)
    return os.path.exists(playbook_path)


def build_pb_path(play_uuid):
    return os.path.join(configuration.settings.playbooks_root_dir,
                        "artifacts",
                        play_uuid)


def writeYAML(data, path_name):
    try:
        with open(path_name, "w") as yaml_file:
            yaml_file.write(yaml.safe_dump(data,
                                           default_flow_style=False,
                                           explicit_start=True))
    except IOError as e:
        return False
    else:
        return True


def loadYAML(path_name):
    with open(path_name, 'r') as yaml_in:
        data = yaml.safe_load(yaml_in)
    return data


class APIResponse(object):
    def __init__(self):
        self.status = ''
        self.msg = ''
        self.data = dict()
