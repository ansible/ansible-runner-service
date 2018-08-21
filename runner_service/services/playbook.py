
import os
import glob
import json
import uuid
import threading
import time

from ansible_runner import run_async
from runner_service import configuration
from .utils import fread

import logging
logger = logging.getLogger(__name__)


def get_status(play_uuid):

    pb_artifacts = os.path.join(configuration.settings.playbooks_root_dir,
                                "artifacts",
                                play_uuid)

    if not os.path.exists(pb_artifacts):
        return None

    pb_status = os.path.join(pb_artifacts,
                             "status")

    if os.path.exists(pb_status):
        return {"status": fread(pb_status)}
    else:
        # get last event
        events_dir = os.path.join(pb_artifacts, "job_events")
        events = os.listdir(events_dir)
        events.sort(key=lambda filenm: int(filenm.split("-", 1)[0]))
        last_event = events[-1]
        last_event_data = json.loads(fread(os.path.join(events_dir,
                                                        last_event)))
        print(last_event_data)
        return {"status": "running",
                "task_id": last_event_data.get('counter'),
                "task_name": last_event_data['event_data'].get('task')}


def list_playbooks():

    pb_dir = os.path.join(configuration.settings.playbooks_root_dir,
                          "project")
    playbook_names = [os.path.basename(pb_path) for pb_path in
                      glob.glob(os.path.join(pb_dir,
                                             "*.yml"))]

    return playbook_names


def stop_playbook(play_uuid):
    return


def start_playbook(playbook_name, vars):
    """ Initiate a playbook run """

    play_uuid = str(uuid.uuid1())

    settings = {"suppress_ansible_output": True}

    # this should just be run_async, using 'run' hangs the root logger output
    # even when backgrounded
    if vars:
        _thread, _runner = run_async(private_data_dir=configuration.settings.playbooks_root_dir,
                                     settings=settings,
                                     # envvars=envvars,
                                     quiet=False,
                                     ident=play_uuid,
                                     extravars=vars,
                                     # inventory='localhost',
                                     playbook=playbook_name)
    else:
        _thread, _runner = run_async(private_data_dir=configuration.settings.playbooks_root_dir,
                                     settings=settings,
                                     # envvars=envvars,
                                     quiet=False,
                                     ident=play_uuid,
                                     # inventory='localhost',
                                     playbook=playbook_name)

    # Workaround for ansible_runner logging, resetting the rootlogger level
    root_logger = logging.getLogger()
    root_logger.setLevel(10)

    delay = 0.1
    timeout = 5 / delay
    ctr = 0

    # Wait for the play to actually start, but apply a timeout
    while _runner.status.lower() == 'unstarted':
        time.sleep(delay)
        ctr += 1
        if ctr > timeout:
            return play_uuid, "timeout"

    # Start a watcher, so the termination of the playbook can be recorded in
    # the log file
    _t = threading.Thread(target=watcher, args=(_thread, _runner))
    _t.daemon = True
    _t.name = "watcher"
    _t.start()

    return play_uuid, _runner.status


def watcher(pb_thread, pb_runner):
    """
    Use a watcher thread to wait for a given playbook execution thread to
    terminate
    """

    pb_thread.join()
    logger.info("Playbook {}, UUID={} ended, "
                "status={}".format(pb_runner.config.playbook,
                                   pb_runner.config.ident,
                                   pb_runner.status))
