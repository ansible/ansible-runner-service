
from flask import make_response

from .base import BaseResource
from ..metrics import PrometheusStats


class PrometheusMetrics(BaseResource):
    """Gather ansible playbook metrics for Prometheus monitoring"""

    def get(self):
        """
        GET
        Return the current performance/usage counters in text format

        Example.
        ```
        $ curl -k --key ./client.key --cert ./client.crt https://localhost:5001/metrics
        #HELP: runner_service_duration_scrape_secs - time taken to gather the data
        #TYPE: runner_service_duration_scrape_secs - gauge
        runner_service_duration_scrape_secs{hostname="rh460p"} 0
        #HELP: runner_service_event_status - event/task states for all playbooks executed since daemon started
        #TYPE: runner_service_event_status - count
        runner_service_event_status{hostname="rh460p",event_status="ok"} 12
        runner_service_event_status{hostname="rh460p",event_status="failed"} 3
        runner_service_event_status{hostname="rh460p",event_status="skipped"} 1
        runner_service_event_status{hostname="rh460p",event_status="unreachable"} 0
        runner_service_event_status{hostname="rh460p",event_status="no_hosts"} 0
        runner_service_event_status{hostname="rh460p",event_status="file_diff"} 0
        runner_service_event_status{hostname="rh460p",event_status="async_failed"} 0
        runner_service_event_status{hostname="rh460p",event_status="async_ok"} 0
        runner_service_event_status{hostname="rh460p",event_status="async_poll"} 0
        #HELP: runner_service_playbook_count - number of playbooks known to the service
        #TYPE: runner_service_playbook_count - gauge
        runner_service_playbook_count{hostname="rh460p"} 3
        #HELP: runner_service_playbooks_active - number of playbook jobs running
        #TYPE: runner_service_playbooks_active - gauge
        runner_service_playbooks_active{hostname="rh460p"} 0
        #HELP: runner_service_playbooks_status - playbook completion states since daemon started
        #TYPE: runner_service_playbooks_status - count
        runner_service_playbooks_status{hostname="rh460p",status="successful"} 1
        runner_service_playbooks_status{hostname="rh460p",status="failed"} 0
        runner_service_playbooks_status{hostname="rh460p",status="canceled"} 0
        runner_service_playbooks_status{hostname="rh460p",status="timeout"} 0
        ```
        """
        stats = PrometheusStats()
        stats.fetch()

        return make_response(stats.formatted, 200)
