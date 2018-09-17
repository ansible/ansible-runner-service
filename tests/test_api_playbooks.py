
import sys
import logging
import requests
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
        response = requests.get("https://localhost:5001/api/v1/playbooks",
                                verify=False)
        self.assertEqual(response.status_code,
                         200)
        payload = response.json()
        self.assertTrue(isinstance(payload['data']['playbooks'], list))

    def test_playbook_status(self):
        """- get playbook state"""
        response = requests.get("https://localhost:5001/api/v1/playbooks/53b955f2-b79a-11e8-8be9-c85b7671906d", # noqa
                                verify=False)
        self.assertEqual(response.status_code,
                         200)
        payload = response.json()
        self.assertTrue(payload['msg'] == "successful")

    def test_run_missing_playbook_(self):
        """- run a dummy playbook - should error 404"""
        response = requests.post("https://localhost:5001/api/v1/playbooks/imnotallthere.yml", # noqa
                                 json={},
                                 verify=False)
        self.assertEqual(response.status_code,
                         404)

    # def test_run_playbook_(self):
    #     """- run a test playbook - and check completion"""
    #     response = requests.post("https://localhost:5001/api/v1/groups/test", # noqa
    #                              verify=False)
    #     self.assertEqual(response.status_code,
    #                      200)
    #     response = requests.post("https://localhost:5001/api/v1/hosts/localhost/groups/test", # noqa
    #                              verify=False)
    #     self.assertEqual(response.status_code,
    #                      200)
    #
    #     response = requests.post("https://localhost:5001/api/v1/playbooks/testplaybook.yml", # noqa
    #                              json={},
    #                              verify=False)
    #     self.assertEqual(response.status_code,
    #                      202)
    #
    #     play_uuid = response.json()['data']['play_uuid']
    #
    #     # wait for it to complete
    #     response = requests.get("https://localhost:5001/api/v1/playbooks/{}".format(play_uuid), # noqa
    #                             verify=False)
    #     print(response.json())


if __name__ == "__main__":

    unittest.main(verbosity=2)
