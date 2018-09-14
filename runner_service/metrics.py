import os
import time
import glob
import socket

from .cache import runner_stats, runner_cache
from runner_service import configuration


class Metric(object):
    """ Metric object used to hold the metric, labels and value """

    def __init__(self, vhelp, vtype):
        self.var_help = vhelp
        self.var_type = vtype
        self.data = []

    def add(self, labels, value):
        _d = dict(labels=labels,
                  value=value)
        self.data.append(_d)


class PrometheusStats(object):

    def __init__(self):
        self.metrics = {}
        self.hostname = socket.gethostname()

    def fetch(self):
        stime = int(time.time())

        self._get_event_counts()
        self._get_playbook_count()
        self._get_playbooks_active()
        self._get_playbooks_status()

        # insert the get calls here
        etime = int(time.time())

        fetch_stats = Metric("time taken to gather the data", "gauge")
        labels = {"hostname": self.hostname}
        fetch_stats.add(labels, etime - stime)
        self.metrics['runner_service_duration_scrape_secs'] = fetch_stats

    @property
    def formatted(self):
        s = ''
        for m_name in sorted(self.metrics.keys()):
            metric = self.metrics[m_name]
            s += "#HELP: {} - {}\n".format(m_name,
                                           metric.var_help)
            s += "#TYPE: {} - {}\n".format(m_name,
                                           metric.var_type)

            for v in metric.data:
                labels = []
                for n in v['labels'].items():
                    label_name = '{}='.format(n[0])
                    label_value = '"{}"'.format(n[1])

                    labels.append('{}{}'.format(label_name,
                                                label_value))

                s += "{}{{{}}} {}\n".format(m_name,
                                            ','.join(labels),
                                            v["value"])

        return s.rstrip()

    def _get_playbook_count(self):
        _m = Metric("number of playbooks known to the service", "gauge")
        labels = {"hostname": self.hostname}
        pb_dir = os.path.join(configuration.settings.playbooks_root_dir,
                              "project")
        playbook_count = len(glob.glob('{}/*.yml'.format(pb_dir)))
        _m.add(labels, playbook_count)
        self.metrics['runner_service_playbook_count'] = _m

    def _get_playbooks_active(self):
        _m = Metric("number of playbook jobs running", "gauge")
        labels = {"hostname": self.hostname}
        active_count = len(runner_cache.keys())
        _m.add(labels, active_count)
        self.metrics['runner_service_playbooks_active'] = _m

    def _get_playbooks_status(self):
        _m = Metric("playbook completion states since daemon started", "count")
        for status in runner_stats.playbook_status.keys():
            labels = {"hostname": self.hostname, "status": status}
            _m.add(labels, runner_stats.playbook_status[status])
        self.metrics['runner_service_playbooks_status'] = _m

    def _get_event_counts(self):
        _m = Metric("event/task states for all playbooks executed since "
                    "daemon started", "count")
        for status in runner_stats.event_stats.keys():
            labels = {"hostname": self.hostname, "event_status": status}
            _m.add(labels, runner_stats.event_stats[status])
        self.metrics['runner_service_event_status'] = _m
