
import sys
import json
import logging
import unittest

sys.path.extend(["../", "./"])
from common import APITestCase  # noqa


# turn of normal logging that the ansible_runner_service will generate
nh = logging.NullHandler()
r = logging.getLogger()
r.addHandler(nh)


class TestJobEvents(APITestCase):

    def test_list_job_events(self):
        """- list events from the sample playbook run"""
        response = self.app.get('api/v1/jobs/53b955f2-b79a-11e8-8be9-c85b7671906d/events')  # noqa

        self.assertEqual(response.status_code,
                         200)
        payload = json.loads(response.data)
        self.assertEqual(payload['data']['total_events'],
                         49)

    def test_list_invalid_job(self):
        """- list events for a playbook run that doesn't exist - error 404"""
        response = self.app.get("api/v1/jobs/93b955f2-b79a-11e8-8be9-c85b76719093/events")    # noqa

        self.assertEqual(response.status_code,
                         404)

    def test_fetch_single_event(self):
        """- fetch a single event by event uuid"""
        response = self.app.get("api/v1/jobs/53b955f2-b79a-11e8-8be9-c85b7671906d/events/49-e084d030-cd3d-4c76-a4d3-03d032c4dc8f")  # noqa

        self.assertEqual(response.status_code,
                         200)
        self.assertEqual(response.headers['Content-Type'],
                         'application/json')
        self.assertIn("event_data", json.loads(response.data)['data'])

    def test_fetch_invalid_event(self):
        """- attempt to fetch an invalid event - error 404"""
        response = self.app.get("api/v1/jobs/53b955f2-b79a-11e8-8be9-c85b7671906d/events/49-9384d030-cd3d-4c76-a4d3-03d032c4dc93")  # noqa

        self.assertEqual(response.status_code,
                         404)

    def test_get_event_with_filter(self):
        """- use filter to find matching events in a playbook run"""
        response = self.app.get("api/v1/jobs/53b955f2-b79a-11e8-8be9-c85b7671906d/events?task=RESULTS")    # noqa

        self.assertEqual(response.status_code,
                         200)
        self.assertEqual(response.headers['Content-Type'],
                         'application/json')

        payload = json.loads(response.data)
        self.assertIn("events", payload['data'])
        self.assertEqual(payload['data']['total_events'],
                         1)
        self.assertEqual(payload['data']['events']['49-e084d030-cd3d-4c76-a4d3-03d032c4dc8f']['task'],  # noqa
                         "RESULTS")

    def test_get_event_with_invalid_filter(self):
        """- use filter that doesn't match any event"""
        response = self.app.get("api/v1/jobs/53b955f2-b79a-11e8-8be9-c85b7671906d/events?task=MISSING") # noqa

        self.assertEqual(response.status_code,
                         200)
        payload = json.loads(response.data)
        self.assertIn("events", payload['data'])
        self.assertEqual(payload['data']['total_events'],
                         0)


if __name__ == "__main__":

    unittest.main(verbosity=2)
