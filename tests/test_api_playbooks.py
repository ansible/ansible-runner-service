
import sys
import json
import time
import logging
import unittest

sys.path.extend(["../", "./"])
from common import APITestCase                # noqa

# turn of normal logging that the ansible_runner_service will generate
nh = logging.NullHandler()
r = logging.getLogger()
r.addHandler(nh)


class TestPlaybooks(APITestCase):

    def test_get_playbooks(self):
        """- Get a list of managed playbooks"""
        response = self.app.get('api/v1/playbooks')
        self.assertEqual(response.status_code,
                         200)

        payload = json.loads(response.data)
        self.assertTrue(isinstance(payload['data']['playbooks'], list))

    def test_playbook_status(self):
        """- get playbook state"""
        response = self.app.get('api/v1/playbooks/53b955f2-b79a-11e8-8be9-c85b7671906d')    # noqa
        self.assertEqual(response.status_code,
                         200)

        payload = json.loads(response.data)
        self.assertTrue(payload['msg'] == "successful")

    def test_invalid_playbook_status(self):
        """- get playbook state for a non-existant playbook run"""
        response = self.app.get('api/v1/playbooks/9353b955f2-b79a-11e8-8be9-c85b76719093')  # noqa

        self.assertEqual(response.status_code,
                         404)

    def test_run_missing_playbook_(self):
        """- run a dummy playbook - should error 404"""
        response = self.app.post('api/v1/playbooks/imnotallthere.yml',
                                 data=json.dumps(dict()),
                                 content_type='application/json')
        self.assertEqual(response.status_code,
                         404)

    def test_cancel_nonactive_playbook(self):
        """- attempt to cancel a playbook that isn't running"""
        response = self.app.delete('api/v1/playbooks/9353b955f2-b79a-11e8-8be9-c85b76719093')   # noqa
        self.assertEqual(response.status_code,
                         404)

if __name__ == "__main__":

    unittest.main(verbosity=2)
