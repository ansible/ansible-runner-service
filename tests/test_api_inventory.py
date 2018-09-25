
import os
import sys
import yaml
import logging
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
        response = self.get('/groups')

        self.assertEqual(response.status_code,
                         200)
        self.assertEqual(response.headers['Content-Type'],
                         'application/json')

        payload = response.json()
        self.assertIn('groups', payload['data'].keys())
        self.assertTrue(isinstance(payload['data']['groups'], list))

    def test_group_add(self):
        """- Add a group to the inventory"""
        response = self.post('/groups/group1')

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
        response = self.post('/groups/group2')
        self.assertEqual(response.status_code,
                         200)

        response = self.delete('/groups/group2')
        self.assertEqual(response.status_code,
                         200)

        root_dir = os.getcwd()
        inv_filename = os.path.join(root_dir, 'samples/inventory/hosts')
        inv_data = yaml.safe_load(fread(inv_filename))
        self.assertNotIn("group2", inv_data['all']['children'].keys())

    def test_host_add(self):
        """- Add a host to a group - 404 unless ssh_checks turned off"""

        response = self.post('/groups/newhost')
        self.assertEqual(response.status_code,
                         200)

        response = self.post("/hosts/dummy/groups/newhost")

        if TestInventory.config.ssh_checks:

            self.assertEqual(response.status_code,
                             404)
            payload = response.json()
            self.assertTrue(payload['status'] == 'NOCONN')
        else:
            self.assertEqual(response.status_code,
                             200)
            payload = response.json()
            self.assertTrue(payload['msg'].upper().startswith('SKIPPED'))

    def test_host_add_localhost(self):
        """- Add a localhost to a group"""

        response = self.post('/groups/local')
        self.assertEqual(response.status_code,
                         200)

        response = self.post('/hosts/localhost/groups/local')
        self.assertEqual(response.status_code,
                         200)

        root_dir = os.getcwd()
        inv_filename = os.path.join(root_dir, 'samples/inventory/hosts')
        inv_data = yaml.safe_load(fread(inv_filename))
        self.assertIn("localhost", inv_data['all']['children']['local']['hosts'].keys()) # noqa

    def test_hosts(self):
        """- Get a list of hosts in the inventory"""
        response = self.get('/hosts')
        self.assertEqual(response.status_code,
                         200)

        payload = response.json()
        self.assertTrue(isinstance(payload['data']['hosts'], list))


if __name__ == "__main__":

    unittest.main(verbosity=2)
