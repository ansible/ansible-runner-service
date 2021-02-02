
import os
import glob
import uuid
import time
import datetime
import getpass

from ansible_runner import run_async
from ansible_runner.exceptions import AnsibleRunnerException
from runner_service import configuration
from runner_service.cache import runner_cache, runner_stats
from .utils import APIResponse
from ..utils import fread

from ..cache import event_cache

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
            "task_metadata": runner_cache[play_uuid]['current_task_metadata'],
            "role": runner_cache[play_uuid]['role'],
            "last_task_num": runner_cache[play_uuid]['last_task_num'],
            "skipped": runner_cache[play_uuid]['skipped'],
            "failed": runner_cache[play_uuid]['failed'],
            "ok": runner_cache[play_uuid]['ok'],
            "failures": runner_cache[play_uuid]['failures']
        }

        logger.debug("runner_cache 'hit' for playbook status request")
        return r
    else:
        logger.debug("runner_cache 'miss' for run {}".format(play_uuid))

        # Status is against a playbook that has finished and has been removed
        # from cache, so we need to look at the artifacts dir
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
    r.msg = "{} playbook found".format(len(playbook_names))
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
    any tidy or reporting tasks

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

    runner_cache[runner.config.ident]['status'] = runner.status

    prune_runner_cache(runner.config.ident)


def prune_runner_cache(current_runner):
    if len(runner_cache.keys()) >= configuration.settings.runner_cache_size:
        logger.debug("Maintaining runner_cache entries")
        logger.info("Dropping finished runner object for play uuid {} from "
                    "runner_cache".format(current_runner))
        del runner_cache[current_runner]


def cb_event_handler(event_data):

    logger.debug("cb_event_handler event_data={}".format(event_data))

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
            runner_cache[ident]['current_task'] = \
                event_data['event_data'].get('task', "Unknown task")
            metadata = event_data['event_data']
            metadata['created'] = event_data['created']
            runner_cache[ident]['current_task_metadata'] = metadata

        runner_cache[ident]['last_task_num'] = event_data['counter']

        # role is not a fixed attribute
        role_value = ''
        if 'role' in event_data:
            role_value =  runner_cache[ident]['role'] = event_data['event_data'].get('role', '') # noqa
        runner_cache[ident]['role'] = role_value

        if event_type.startswith("runner_on_"):
            event_shortname = event_type[10:]
            if event_shortname in runner_cache[ident]:
                runner_cache[ident][event_shortname] += 1
            else:
                runner_cache[ident][event_shortname] = 1
            if event_shortname == 'failed':
                if event_data['event_data'].get('ignore_errors', False):
                    # skip failures reporting if ignore_errors is set
                    runner_cache[ident]['failed'] -= 1
                else:
                    # we have a valid failure to report
                    event_metadata = event_data['event_data']
                    runner_cache[ident]['failures'][event_metadata.get('host')] = event_data # noqa

    # populate the event cache
    if 'runner_ident' in event_data and \
       'uuid' in event_data and ident in event_cache:
        event_cache[ident].update({event_data['uuid']: event_data})

    # regardless return true to ensure the data is written to artifacts dir
    return True


def start_playbook(playbook_name, vars=None, filter=None, tags=None):
    """ Initiate a playbook run """

    r = APIResponse()
    play_uuid = str(uuid.uuid1())

    settings = {"suppress_ansible_output": True}
    local_modules = os.path.join(configuration.settings.playbooks_root_dir,
                                 "library")

    # this should just be run_async, using 'run' hangs the root logger output
    # even when backgrounded

    artifacts_dir = os.path.join(configuration.settings.playbooks_root_dir, "artifacts")
    private_data_dir = os.path.join(artifacts_dir, play_uuid)
    os.makedirs(private_data_dir)
    parms = {
        "private_data_dir": private_data_dir,
        "project_dir": os.path.join(configuration.settings.playbooks_root_dir, 'project'),
        "inventory": os.path.join(configuration.settings.playbooks_root_dir, 'inventory'),
        "artifact_dir": artifacts_dir,
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

    cmdline = []
    if filter.get('check', 'false').lower() == 'true':
        cmdline.append('--check')

    if tags:
        cmdline.append("--tags {}".format(tags))

    if configuration.settings.target_user != getpass.getuser():
        logger.debug("Run the playbook with a user override of "
                     "{}".format(configuration.settings.target_user))
        cmdline.append("--user {}".format(configuration.settings.target_user))

    logger.debug("Run the playbook with a private key override of "
                 "{}".format(configuration.settings.ssh_private_key))
    cmdline.append("--private-key {}".format(configuration.settings.ssh_private_key))

    parms['cmdline'] = ' '.join(cmdline)

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
                               "status": _runner.status,
                               "current_task": None,
                               "current_task_metadata": {
                                    "created": "",
                                    "play_pattern": "",
                                    "task_path": "",
                                    "task_action": ""
                                    },
                               "role": "",
                               "last_task_num": None,
                               "start_epoc": time.time(),
                               "skipped": 0,
                               "failed": 0,
                               "ok": 0,
                               "failures": {}
                               }

    #  add uuid to cache so it can be filled with its events
    event_cache[play_uuid] = {'time': datetime.datetime.now()}
    #  limit event cache size
    if len(event_cache) > configuration.settings.event_cache_size:
        oldest = play_uuid
        for ident in event_cache:
            if event_cache[ident]['time'] < event_cache[oldest]['time']:
                oldest = ident
        del event_cache[oldest]

    return r
