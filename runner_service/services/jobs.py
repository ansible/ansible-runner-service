
import os
import glob
import json
import threading

# conditional import for python 2.7 and python3.6 support
try:
    import Queue as queue
except ImportError:
    import queue

from .utils import APIResponse
from ..utils import fread
from runner_service import configuration

import logging
logger = logging.getLogger(__name__)

ignored_events = [
    'playbook_on_play_start',
    'playbook_on_start',
    'playbook_on_task_start',
    'playbook_on_stats'
]

# Placeholder to use as a means of caching events from recent playbook runs
# to reduce the I/O impact of physically reading from disk
event_cache = {}


def filter_event(event_path, filter):

    event_fname = os.path.basename(event_path)

    if event_fname.endswith("-partial.json"):
        logger.debug("Skipping partial event file: {}".format(event_fname))
        return None

    with open(event_path, 'r') as event_fd:
        try:
            event_info = json.loads(event_fd.read())
        except json.JSONDecodeError as err:
            logger.warning("Invalid JSON within {}..."
                           "skipping".format(event_fname))
            return None

    # if the filter is null, our work here is done!
    if not filter:
        return event_info

    tname = threading.current_thread().name

    if event_info.get('event') in ignored_events:
        logger.debug('[{}] Skipping start/stats event: {}'.format(tname,
                                                                  event_fname))
        return None

    elif 'event_data' in event_info:
        match = True
        for key in filter:
            event_data_key = event_info['event_data'].get(key, None)

            result_data = event_info['event_data'].get('res', None)
            if result_data:
                res_key = event_info['event_data']['res'].get(key, None)
            else:
                res_key = None

            base_key = event_info.get(key, None)

            # check content matches filter
            if filter.get(key) not in [base_key, event_data_key, res_key]:
                match = False
                break

        if match:
            logger.debug("[{}] Filter matched against {}".format(tname,
                                                                 event_fname))
            return event_info
        else:
            logger.debug("[{}] Skipping {} due to filter "
                         "mismatch ".format(tname, event_fname))
            return None

    # the default is to return the event_info
    return event_info


def event_summary(event_info, summary_keys=['host', 'task', 'event']):
    """ Provide a quick overview of the event code_data

    :param event_info: dict/json of a job event
    :param summary_keys: list of fields that represent a summary of the event
                         the event data is checked at the outer level, and in
                         the event_data namespace
    :return: Returns summary metadata for the event
    """

    if summary_keys:
        base = {k: event_info[k] for k in summary_keys if k in event_info}
        event_data = {k: event_info['event_data'][k] for k in summary_keys
                      if k in event_info.get('event_data')}

        # python3.5 an above idiom
        # return {**base, **event_data}
        merged = base.copy()
        merged.update(event_data)
        return merged
    else:
        return event_info


def scan_event_data(work_queue, filter, matched_events):

    tname = threading.current_thread().name
    logger.debug("[{}] Event scanner started".format(tname))
    ctr = 0

    while True:
        try:
            event_path = work_queue.get(block=False)
        except queue.Empty:
            break
        else:
            event_filename = os.path.basename(event_path)
            logger.debug("[{}] Checking {}".format(tname, event_filename))
            event_info = filter_event(event_path, filter)
            if event_info:
                matched_events[event_filename] = event_summary(event_info)
            ctr += 1
            work_queue.task_done()

    logger.debug("[{}] Event scanner ended. Processed "
                 "{} files".format(tname, ctr))


def get_events(pb_path, filter):

    r = APIResponse()

    event_dir = os.path.join(pb_path, "job_events")
    play_uuid = os.path.basename(pb_path)
    _events = os.listdir(event_dir)
    logger.debug("Job events for play {}: {}".format(play_uuid,
                                                     len(_events)))
    logger.debug("Active filter is :{}".format(filter))
    work_queue = queue.Queue()
    for event_file in _events:
        event_path = os.path.join(event_dir, event_file)
        work_queue.put(event_path)

    matched_events = {}
    threads = []
    for ctr in range(0, configuration.settings.event_threads):
        _t = threading.Thread(target=scan_event_data,
                              args=(work_queue, filter, matched_events,))
        _t.daemon = True
        threads.append(_t)
        _t.start()

    # Wait for the queue to signal all items have been processed
    work_queue.join()

    # sort the keys into numeric order
    srtd_keys = sorted(matched_events, key=lambda x: int(x.split('-')[0]))
    r.status, r.data = "OK", {"events": {k[:-5]: matched_events[k]
                                         for k in srtd_keys},
                              "total_events": len(srtd_keys)}

    return r


def get_event(pb_path, event_uuid):
    r = APIResponse()
    event_path = glob.glob(os.path.join(pb_path,
                                        "job_events",
                                        "{}.json".format(event_uuid)))

    if event_path:
        r.status, r.data = "OK", json.loads(fread(event_path[0]))
        return r
    else:
        r.status, r.msg = "NOTFOUND", "Event not found"
        return r
