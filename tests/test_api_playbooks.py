
import sys
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
        response = self.get('/playbooks')
        self.assertEqual(response.status_code,
                         200)

        payload = response.json()
        self.assertTrue(isinstance(payload['data']['playbooks'], list))

    def test_playbook_status(self):
        """- get playbook state"""
        response = self.get('/playbooks/53b955f2-b79a-11e8-8be9-c85b7671906d')
        self.assertEqual(response.status_code,
                         200)

        payload = response.json()
        self.assertTrue(payload['msg'] == "successful")

    def test_invalid_playbook_status(self):
        """- get playbook state for a non-existant playbook run"""
        response = self.get('playbooks/9353b955f2-b79a-11e8-8be9-c85b76719093')
        self.assertEqual(response.status_code,
                         404)

    def test_run_missing_playbook_(self):
        """- run a dummy playbook - should error 404"""
        response = self.post('/playbooks/imnotallthere.yml', payload={})
        self.assertEqual(response.status_code,
                         404)

    def test_run_playbook(self):
        """- start a playbook"""
        # create a playbook group and put localhost in it
        """- Add a host to a group - 404 unless ssh_checks turned off"""
        response = self.post('/groups/playbook')
        self.assertEqual(response.status_code,
                         200)

        response = self.post('/hosts/localhost/groups/playbook')
        self.assertEqual(response.status_code,
                         200)

        response = self.post('/playbooks/testplaybook.yml',
                             payload={})
        self.assertEqual(response.status_code, 202)     # it started OK

        play_uuid = response.json()['data']['play_uuid']
        # wait for playbook completion
        while True:
            response = self.get('/playbooks/{}'.format(play_uuid))

            self.assertIn(response.status_code, [200, 404])
            if response.json()['msg'] in ['failed', 'successful']:
                break
            time.sleep(0.5)


if __name__ == "__main__":

    unittest.main(verbosity=2)
