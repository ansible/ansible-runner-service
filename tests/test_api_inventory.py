
import os
import sys
import yaml
import logging
import requests
import unittest

sys.path.extend(["../", "./"])
from common import APITestCase              # noqa
from runner_service.utils import fread      # noqa

# turn of normal logging that the ansible_runner_service will generate
nh = logging.NullHandler()
r = logging.getLogger()
r.addHandler(nh)


class TestInventory(APITestCase):

    def test_groups(self):
        """- Get a list of groups from the inventory"""

        response = requests.get("https://localhost:5001/api/v1/groups",
                                verify=False)

        self.assertEqual(response.status_code,
                         200)
        self.assertEqual(response.headers['Content-Type'],
                         'application/json')

        payload = response.json()
        self.assertIn('groups', payload['data'].keys())
        self.assertTrue(isinstance(payload['data']['groups'], list))

    def test_group_add(self):
        """- Add a group to the inventory"""
        response = requests.post("https://localhost:5001/api/v1/groups/group1",
                                 verify=False)
        self.assertEqual(response.status_code,
                         200)
        self.assertEqual(response.headers['Content-Type'],
                         'application/json')

        root_dir = os.getcwd()
        inv_filename = os.path.join(root_dir, 'samples/inventory/hosts')
        inv_data = yaml.safe_load(fread(inv_filename))
        self.assertIn("group1", inv_data['all']['children'].keys())

    def test_group_remove(self):
        """- Remove a group from the inventory"""
        # first, setup the group we're going to remove
        response = requests.post("https://localhost:5001/api/v1/groups/group2",
                                 verify=False)
        self.assertEqual(response.status_code,
                         200)

        response = requests.delete("https://localhost:5001/api/v1/groups/group2",   # noqa
                                   verify=False)
        self.assertEqual(response.status_code,
                         200)

        root_dir = os.getcwd()
        inv_filename = os.path.join(root_dir, 'samples/inventory/hosts')
        inv_data = yaml.safe_load(fread(inv_filename))
        self.assertNotIn("group2", inv_data['all']['children'].keys())

    def test_host_add(self):
        """- Add a host to a group - expecting 404 NOCONN error"""
        response = requests.post("https://localhost:5001/api/v1/groups/newhost",    # noqa
                                 verify=False)
        self.assertEqual(response.status_code,
                         200)
        response = requests.post("https://localhost:5001/api/v1/hosts/dummy/groups/newhost",    # noqa
                                 verify=False)
        self.assertEqual(response.status_code,
                         404)

        payload = response.json()
        self.assertTrue(payload['status'] == 'NOCONN')

    def test_host_add_localhost(self):
        """- Add a localhost to a group"""
        response = requests.post("https://localhost:5001/api/v1/groups/local",
                                 verify=False)
        self.assertEqual(response.status_code,
                         200)
        response = requests.post("https://localhost:5001/api/v1/hosts/localhost/groups/local",    # noqa
                                 verify=False)
        self.assertEqual(response.status_code,
                         200)

        root_dir = os.getcwd()
        inv_filename = os.path.join(root_dir, 'samples/inventory/hosts')
        inv_data = yaml.safe_load(fread(inv_filename))
        self.assertIn("localhost", inv_data['all']['children']['local']['hosts'].keys()) # noqa

    def test_hosts(self):
        """- Get a list of hosts in the inventory"""
        response = requests.get("https://localhost:5001/api/v1/hosts",
                                verify=False)
        self.assertEqual(response.status_code,
                         200)
        payload = response.json()
        self.assertTrue(isinstance(payload['data']['hosts'], list))


if __name__ == "__main__":

    unittest.main(verbosity=2)
