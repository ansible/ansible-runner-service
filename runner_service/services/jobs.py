
import os
import glob
import json
from .utils import fread

import logging
logger = logging.getLogger(__name__)

ignored_events = [
    'playbook_on_play_start',
    'playbook_on_start',
    'playbook_on_task_start',
    'playbook_on_stats'
]


def filtered_event(event_path, filter):

    with open(event_path, 'r') as event_fd:
        try:
            event_info = json.loads(event_fd.read())
        except:
            # TODO invalid json?
            pass

    if event_info.get('event') in ignored_events:
        logger.debug('Event filter skipping {}'.format(event_path))
        return None
    elif 'event_data' in event_info:
        match = True
        for key in filter:
            event_data_key = event_info['event_data'].get(key, None)
            res_key = event_info['event_data']['res'].get(key, None)
            base_key = event_info.get(key, None)

            # check content matches filter
            if event_data_key != filter.get(key):
                logger.debug("Skipping due to filter mismatch "
                             "on '{}' - ".format(key,
                                                 event_info.get('event_data')[key]))
                match = False
                break

        if match:
            return event_info

    return None


def get_events(pb_path, filter):

    _events = os.listdir(os.path.join(pb_path,
                                      "job_events"))
    if filter:
        events = []
        for event in _events:
            event_path = os.path.join(pb_path, "job_events", event)
            event_info = filtered_event(event_path, filter)
            if event_info:
                # could pull entries from event_info to make the returned
                # list more usable?
                events.append(event)
    else:
        events = _events

    if events:
        return sorted([fname[:-5] for fname in events])
    else:
        # TODO need a distinction here for the return value, if the filter excludes
        # everything != no event files found
        logger.debug("No events found within {}".format(pb_path))
        return None


def get_event(pb_path, event_uuid):

    event_path = glob.glob(os.path.join(pb_path,
                                        "job_events",
                                        "{}.json".format(event_uuid)))

    if event_path:
        return json.loads(fread(event_path[0]))
    else:
        return None
