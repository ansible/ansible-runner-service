
from .base import BaseResource


class PrometheusMetrics(BaseResource):
    """Gather ansible playbook metrics for Prometheus monitoring"""

    def get(self):
        """
        GET
        Return the current performance counters in text format
        """
        return {"message": "Metrics endpoint not implemented"}, 501
