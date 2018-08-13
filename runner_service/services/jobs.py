
import os
import glob
import json
from .utils import fread

import logging
logger = logging.getLogger(__name__)


def get_events(pb_path):

    events = os.listdir(os.path.join(pb_path,
                                     "job_events"))

    if events:
        return sorted([fname[:-5] for fname in events])
    else:
        return None


def get_event(pb_path, event_uuid):

    event_path = glob.glob(os.path.join(pb_path,
                                        "job_events",
                                        "{}.json".format(event_uuid)))

    if event_path:
        return json.loads(fread(event_path[0]))
    else:
        return None
