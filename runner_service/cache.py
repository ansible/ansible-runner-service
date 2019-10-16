from collections import defaultdict

# define dict based variables to act as caches across other modules

class RunnerStats(object):

    playbook_status = {
        "successful": 0,
        "failed": 0,
        "canceled": 0,
        "timeout": 0}

    event_stats = {
        "ok": 0,
        "failed": 0,
        "skipped": 0,
        "unreachable": 0,
        "no_hosts": 0,
        "file_diff": 0,
        "async_failed": 0,
        "async_ok": 0,
        "async_poll": 0}


event_cache = {}

runner_cache = defaultdict(dict)

runner_stats = RunnerStats()
