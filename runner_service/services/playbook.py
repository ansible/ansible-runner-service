
import os
import glob
import json
import uuid
import time

from ansible_runner import run_async
from runner_service import configuration
from .utils import fread, cleanup_dir, APIResponse

# from .jobs import event_cache

import logging
logger = logging.getLogger(__name__)


def get_status(play_uuid):
    r = APIResponse()
    pb_artifacts = os.path.join(configuration.settings.playbooks_root_dir,
                                "artifacts",
                                play_uuid)

    if not os.path.exists(pb_artifacts):
        r.status, r.msg = "NOTFOUND", "Playbook run with UUID {} not found".format(play_uuid)
        return r

    pb_status = os.path.join(pb_artifacts,
                             "status")

    if os.path.exists(pb_status):
        # playbook execution has finished
        r.status, r.msg = "OK", fread(pb_status)
        return r
    else:
        # play is still active
        # get last event
        events_dir = os.path.join(pb_artifacts, "job_events")
        events = os.listdir(events_dir)
        events.sort(key=lambda filenm: int(filenm.split("-", 1)[0]))
        last_event = events[-1]
        last_event_data = json.loads(fread(os.path.join(events_dir,
                                                        last_event)))
        r.status, r.msg = "OK", "Playbook with UUID {} is active".format(play_uuid)
        r.data = {"task_id": last_event_data.get('counter'),
                  "task_name": last_event_data['event_data'].get('task')
                  }
        return r


def list_playbooks():

    r = APIResponse()
    pb_dir = os.path.join(configuration.settings.playbooks_root_dir,
                          "project")
    playbook_names = [os.path.basename(pb_path) for pb_path in
                      glob.glob(os.path.join(pb_dir,
                                             "*.yml"))]
    r.status, r.data = "OK", {"playbooks": playbook_names}

    return r


def stop_playbook(play_uuid):
    return


def cb_playbook_finished(runner):
    """ Report on playbook end state

    This function is called at the end of the invoked playbook to perform
    any tidy or or reporting tasks

    :param runner:  instance of ansible_runner.Runner for the playbook that has
                    just completed
    """
    logger.info("Playbook {}, UUID={} ended, "
                "status={}".format(runner.config.playbook,
                                   runner.config.ident,
                                   runner.status))
    logger.info("Playbook {} Stats: {}".format(runner.config.playbook,
                                               runner.stats))


# Placeholder for populating the event_cache
def cb_event_handler(event_data):
    return True


def start_playbook(playbook_name, vars=None, filter=None):
    """ Initiate a playbook run """

    r = APIResponse()
    play_uuid = str(uuid.uuid1())

    settings = {"suppress_ansible_output": True}
    local_modules = os.path.join(configuration.settings.playbooks_root_dir,
                                 "library")

    # this should just be run_async, using 'run' hangs the root logger output
    # even when backgrounded
    parms = {
        "private_data_dir": configuration.settings.playbooks_root_dir,
        "settings": settings,
        "finished_callback": cb_playbook_finished,
        "event_handler": cb_event_handler,
        "quiet": False,
        "ident": play_uuid,
        "playbook": playbook_name
    }

    if os.path.exists(local_modules):
        parms["envvars"] = {
            "ANSIBLE_LIBRARY": local_modules
        }

    if vars:
        parms['extravars'] = vars

    limit_hosts = filter.get('limit', None)
    if limit_hosts:
        parms['limit'] = limit_hosts

    logger.debug("clearing up old env directory")
    cleanup_dir(os.path.join(configuration.settings.playbooks_root_dir,
                             "env"))

    _thread, _runner = run_async(**parms)

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
            r.status, r.msg = "TIMEOUT", "Timeout hit while waiting for " \
                                         "playbook to start"
            return r

    logger.debug("Playbook {} started in {}s".format(play_uuid,
                                                     ctr * delay))

    r.status, r.data = "OK", {"status": _runner.status,
                              "play_uuid": play_uuid}
    return r
