import os
import glob
import runner_service.configuration as configuration
from runner_service.utils import rm_r


def fread(file_path):
    """ return the contents of the given file """
    with open(file_path, 'r') as file_fd:
        return file_fd.read().strip()


def playbook_exists(playbook_name):
    playbook_path = os.path.join(configuration.settings.playbooks_root_dir,
                                 "project",
                                 playbook_name)
    return os.path.exists(playbook_path)


def build_pb_path(play_uuid):
    return os.path.join(configuration.settings.playbooks_root_dir,
                        "artifacts",
                        play_uuid)


def cleanup_dir(dir_name, exclude=['ssh_key', 'ssh_key.pub']):
    for _path_name in glob.glob("{}/*".format(dir_name)):
        if os.path.basename(_path_name) not in exclude:
            rm_r(_path_name)


class APIResponse(object):
    def __init__(self):
        self.status = ''
        self.msg = ''
        self.data = dict()
