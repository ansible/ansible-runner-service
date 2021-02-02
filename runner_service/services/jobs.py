
import os
import glob
import json
import threading
import datetime

# conditional import for python 2.7 and python3.6 support
try:
    import Queue as queue
except ImportError:
    import queue

from .utils import APIResponse, build_pb_path
from ..utils import fread
from runner_service import configuration
from ..cache import event_cache

import logging
logger = logging.getLogger(__name__)

ignored_events = [
    'playbook_on_play_start',
    'playbook_on_start',
    'playbook_on_task_start',
    'playbook_on_stats'
]


def get_event_info(event_path):
    event_fname = os.path.basename(event_path)

    if event_fname.endswith("-partial.json") or event_fname.endswith("-partial.json.tmp"):
        logger.debug("Skipping partial event file: {}".format(event_fname))
        return None

    with open(event_path, 'r') as event_fd:
        try:
            event_info = json.loads(event_fd.read())
            return event_info
        except json.JSONDecodeError as err:
            logger.warning("Invalid JSON within {}..."
                           "skipping".format(event_fname))
            return None


def filter_event(event_info, filter):

    # if the filter is null, our work here is done!
    if not filter:
        return event_info

    tname = threading.current_thread().name
    event_fname = str(event_info['counter']) + '-' + event_info['uuid']

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


def event_summary(event_info, summary_keys=['host', 'task', 'role', 'event']):
    """ Provide a quick overview of the event code_data

    :param event_info: dict/json of a job event
    :param summary_keys: list of fields that represent a summary of the event
                         the event data is checked at the outer level, and in
                         the event_data namespace
    :return: Returns summary metadata for the event
    """

    if summary_keys:
        base = {k: event_info[k] for k in summary_keys if k in event_info}

        event_data = {}
        if 'event_data' in event_info:
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
            event_info = get_event_info(event_path)
            event_info = filter_event(event_info, filter)
            if event_info:
                matched_events[event_filename] = event_summary(event_info)
            ctr += 1
            work_queue.task_done()

    logger.debug("[{}] Event scanner ended. Processed "
                 "{} files".format(tname, ctr))


def get_events(play_uuid, filter):

    r = APIResponse()
    matched_events = {}

    #  use cache if possible
    if play_uuid in event_cache:
        local_cache = event_cache.copy()
        events = list(local_cache[play_uuid].values())
        logger.debug("Job events for play {}: {}".format(play_uuid,
                                                         len(events) - 1))
        logger.debug("Active filter is :{}".format(filter))

        for event_info in events:
            if type(event_info) is not datetime.datetime:
                event_info = filter_event(event_info, filter)
                if event_info:
                    event_filename = str(event_info['counter']) + '-' + event_info['uuid']
                    matched_events[event_filename] = event_summary(event_info)

        # sort the keys into numeric order
        srtd_keys = sorted(matched_events, key=lambda x: int(x.split('-')[0]))
        r.status, r.data = "OK", {"events": {k: matched_events[k]
                                             for k in srtd_keys},
                                  "total_events": len(srtd_keys)}

        return r

    #  revert to io
    pb_path = build_pb_path(play_uuid)

    if not os.path.exists(pb_path):
        r.status, r.msg = "NOTFOUND", "playbook uuid given does not exist"
        return r

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


def get_event(play_uuid, event_uuid):
    r = APIResponse()

    #  try to use cache first
    cut_event_uuid = event_uuid.split('-', 1)[1]
    if play_uuid in event_cache:
        if cut_event_uuid in event_cache[play_uuid]:
            r.status, r.data = "OK", event_cache[play_uuid][cut_event_uuid]
            return r

    #  revert to io
    pb_path = build_pb_path(play_uuid)
    event_path = glob.glob(os.path.join(pb_path,
                                        "job_events",
                                        "{}.json".format(event_uuid)))

    if event_path:
        r.status, r.data = "OK", json.loads(fread(event_path[0]))
        return r
    else:
        r.status, r.msg = "NOTFOUND", "Event not found"
        return r
