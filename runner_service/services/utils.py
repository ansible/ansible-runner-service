import os
import runner_service.configuration as configuration


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
