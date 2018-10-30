
import os
import glob
import uuid
import time


from ansible_runner import run_async
from ansible_runner.exceptions import AnsibleRunnerException
from runner_service import configuration
from runner_service.cache import runner_cache, runner_stats
from .utils import cleanup_dir, APIResponse
from ..utils import fread

from .jobs import event_cache

import logging
logger = logging.getLogger(__name__)


def get_status(play_uuid):
    r = APIResponse()

    if play_uuid in runner_cache:
        # this is an active playbook, so just use the cache to indicate state
        runner = runner_cache[play_uuid]['runner']
        r.status, r.msg = "OK", runner.status

        r.data = {
            "task": runner_cache[play_uuid]['current_task'],
            "last_task_num": runner_cache[play_uuid]['last_task_num']
        }

        logger.debug("runner_cache 'hit' for playbook status request")
        return r
    else:
        logger.debug("runner_cache 'miss' for run {}".format(play_uuid))

    # Status is against a playbook that has finished, so we need to look at
    # the artifacts dir
    pb_artifacts = os.path.join(configuration.settings.playbooks_root_dir,
                                "artifacts",
                                play_uuid)

    if not os.path.exists(pb_artifacts):
        r.status, r.msg = "NOTFOUND", \
                          "Playbook with UUID {} not found".format(play_uuid)
        logger.info("Request for playbook state had non-existent "
                    "play_uuid '{}'".format(play_uuid))
        return r

    pb_status = os.path.join(pb_artifacts,
                             "status")

    if os.path.exists(pb_status):
        # playbook execution has finished
        r.status, r.msg = "OK", fread(pb_status)
        return r
    else:
        r.status, r.msg = "UNKNOWN", \
                          "The artifacts directory is incomplete!"
        logger.warning("Status Request for Play uuid '{}', found an incomplete"
                       " artifacts directory...Possible ansible_runner "
                       " error?".format(play_uuid))
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
    logger.info("Cancel request for {} issued".format(play_uuid))
    _runner = runner_cache[play_uuid].get('runner')
    _runner.canceled = True
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
    try:
        stats = runner.stats
    except AnsibleRunnerException as err:
        stats = err
    finally:
        logger.info("Playbook {} Stats: {}".format(runner.config.playbook,
                                                   stats))

    if runner.status in runner_stats.playbook_status:
        runner_stats.playbook_status[runner.status] += 1
    else:
        runner_stats.playbook_status[runner.status] = 1

    logger.debug("Dropping runner object from runner_cache")
    del runner_cache[runner.config.ident]


# Placeholder for populating the event_cache
def cb_event_handler(event_data):

    # first look at the event to track overall stats in the runner_stats object
    event_type = event_data.get('event', None)
    if event_type.startswith("runner_on_"):
        event_shortname = event_type[10:]
        if event_shortname in runner_stats.event_stats:
            runner_stats.event_stats[event_shortname] += 1
        else:
            runner_stats.event_stats[event_shortname] = 1

    # maintain the current state of any inflight playbook
    ident = event_data.get('runner_ident', None)
    if ident:
        if event_type == "playbook_on_task_start":
            runner_cache[ident]['current_task'] = event_data['event_data'].get('task', None)    # noqa
        runner_cache[ident]['last_task_num'] = event_data['counter']

    #  fill event cache with data
    event_cache[ident].update({event_data['uuid']: event_data})

    # regardless return true to ensure the data is written to artifacts dir
    return True


def add_tags(tags):

    cmd_file = os.path.join(configuration.settings.playbooks_root_dir,
                            "env", "cmdline")
    tags_param = " --tags {}".format(tags)
    logger.debug("Creating env/cmdline file with tags: {}".format(tags_param))
    with open(cmd_file, "w") as cmdline:
        cmdline.write(tags_param)


def start_playbook(playbook_name, vars=None, filter=None, tags=None):
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

    logger.debug("Clearing up old env directory")
    cleanup_dir(os.path.join(configuration.settings.playbooks_root_dir,
                             "env"))

    if tags:
        add_tags(tags)

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

    runner_cache[play_uuid] = {"runner": _runner,
                               "current_task": None,
                               "last_task_num": None}

    #  add uuid to cache so it can be filled with its events
    event_cache[play_uuid] = {}

    return r
