
import os
import sys
import json
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

        response = self.app.get('api/v1/groups',
                                headers=self.token_header())

        self.assertEqual(response.status_code,
                         200)
        self.assertEqual(response.headers['Content-Type'],
                         'application/json')

        payload = json.loads(response.data)
        self.assertIn('groups', payload['data'].keys())
        self.assertTrue(isinstance(payload['data']['groups'], list))

    def test_group_add(self):
        """- Add a group to the inventory"""

        response = self.app.post('api/v1/groups/group1',
                                 headers=self.token_header())

        self.assertEqual(response.status_code,
                         200)
        self.assertEqual(response.headers['Content-Type'],
                         'application/json')

        root_dir = os.getcwd()
        inv_filename = os.path.join(root_dir, 'samples/inventory/hosts')
        inv_data = yaml.safe_load(fread(inv_filename))
        self.assertIn("group1", inv_data['all']['children'].keys())

    def test_group_add_clash(self):
        """- add a group that already exists"""
        response = self.app.post('api/v1/groups/clash',
                                 headers=self.token_header())

        self.assertEqual(response.status_code,
                         200)

        response = self.app.post('api/v1/groups/clash',
                                 headers=self.token_header())

        self.assertEqual(response.status_code,
                         200)

    def test_group_remove(self):
        """- Remove a group from the inventory"""
        # first, setup the group we're going to remove
        response = self.app.post('api/v1/groups/group2',
                                 headers=self.token_header())
        self.assertEqual(response.status_code,
                         200)

        response = self.app.delete('api/v1/groups/group2',
                                   headers=self.token_header())
        self.assertEqual(response.status_code,
                         200)

        root_dir = os.getcwd()
        inv_filename = os.path.join(root_dir, 'samples/inventory/hosts')
        inv_data = yaml.safe_load(fread(inv_filename))
        self.assertNotIn("group2", inv_data['all']['children'].keys())

    def test_remove_invalid_group(self):
        """- Attempt a group remove with an invalid group name"""
        response = self.app.delete('api/v1/groups/notthere',
                                   headers=self.token_header())
        self.assertEqual(response.status_code,
                         400)

    def test_host_add(self):
        """- Add a host to a group - 404 unless ssh_checks turned off"""

        response = self.app.post('api/v1/groups/newhost',
                                 headers=self.token_header())
        self.assertEqual(response.status_code,
                         200)

        response = self.app.post("api/v1/hosts/dummy/groups/newhost",
                                 headers=self.token_header())

        if TestInventory.config.ssh_checks:

            self.assertEqual(response.status_code,
                             404)
            payload = json.loads(response.data)
            self.assertTrue(payload['status'] == 'NOCONN')
        else:
            self.assertEqual(response.status_code,
                             200)
            payload = json.loads(response.data)
            self.assertTrue(payload['msg'].upper().startswith('SKIPPED'))

    def test_host_add_localhost(self):
        """- Add a localhost to a group"""

        response = self.app.post('api/v1/groups/local',
                                 headers=self.token_header())
        self.assertEqual(response.status_code,
                         200)

        response = self.app.post('/api/v1/hosts/localhost/groups/local',
                                 headers=self.token_header())
        self.assertEqual(response.status_code,
                         200)

        root_dir = os.getcwd()
        inv_filename = os.path.join(root_dir, 'samples/inventory/hosts')
        inv_data = yaml.safe_load(fread(inv_filename))
        self.assertIn("localhost", inv_data['all']['children']['local']['hosts'].keys()) # noqa

    def test_host_add_nogroup(self):
        """- Attempt a host add call with a non-existent group"""
        response = self.app.post('/api/v1/hosts/localhost/groups/biteme',
                                 headers=self.token_header())
        self.assertEqual(response.status_code,
                         400)

    def test_host_add_duplicate(self):
        """- Attempt to add a host multiple times to a group"""
        dupe_count = 2
        response = self.app.post('api/v1/groups/dupe',
                                 headers=self.token_header())
        self.assertEqual(response.status_code,
                         200)

        # seed the group
        response = self.app.post('/api/v1/hosts/localhost/groups/dupe',
                                 headers=self.token_header())
        self.assertEqual(response.status_code,
                         200)

        # attempt to add duplicates
        for _ctr in range(0, dupe_count, 1):

            response = self.app.post('/api/v1/hosts/localhost/groups/dupe',
                                     headers=self.token_header())
            self.assertEqual(response.status_code,
                             200)
            msg = json.loads(response.data)['msg']
            self.assertIn("Host already in the group", msg)

    def test_hosts(self):
        """- Get a list of hosts in the inventory"""
        response = self.app.get('api/v1/hosts',
                                headers=self.token_header())
        self.assertEqual(response.status_code,
                         200)

        payload = json.loads(response.data)
        self.assertTrue(isinstance(payload['data']['hosts'], list))

    def test_remove_valid_host(self):
        """- remove a host from a group"""
        response = self.app.post('api/v1/groups/temphost',
                                 headers=self.token_header())
        self.assertEqual(response.status_code,
                         200)

        response = self.app.post('/api/v1/hosts/localhost/groups/temphost',
                                 headers=self.token_header())
        self.assertEqual(response.status_code,
                         200)

        response = self.app.delete('/api/v1/hosts/localhost/groups/temphost',
                                   headers=self.token_header())
        self.assertEqual(response.status_code,
                         200)

    def test_remove_invalid_host(self):
        """- attempt to remove a host that is not in a specific group"""
        response = self.app.post('api/v1/groups/invalidhost',
                                 headers=self.token_header())
        self.assertEqual(response.status_code,
                         200)

        response = self.app.delete('/api/v1/hosts/notthere/groups/invalidhost',
                                   headers=self.token_header())
        self.assertEqual(response.status_code,
                         400)

    def test_check_membership(self):
        """- show groups host is a member of"""
        response = self.app.post('api/v1/groups/groupone',
                                 headers=self.token_header())
        self.assertEqual(response.status_code,
                         200)
        response = self.app.post('api/v1/hosts/localhost/groups/groupone',
                                 headers=self.token_header())
        self.assertEqual(response.status_code,
                         200)
        response = self.app.get('api/v1/hosts/localhost',
                                headers=self.token_header())
        self.assertEqual(response.status_code,
                         200)
        payload = json.loads(response.data)
        self.assertIn("groupone", payload['data']['groups'])

    def test_show_group_members(self):
        """- show hosts that are members of a specific group"""
        response = self.app.post('api/v1/groups/grouptwo',
                                 headers=self.token_header())
        self.assertEqual(response.status_code,
                         200)

        response = self.app.post('api/v1/hosts/localhost/groups/grouptwo',
                                 headers=self.token_header())
        self.assertEqual(response.status_code,
                         200)

        response = self.app.get('api/v1/groups/grouptwo',
                                headers=self.token_header())
        self.assertEqual(response.status_code,
                         200)
        payload = json.loads(response.data)
        self.assertTrue(isinstance(payload['data']['members'], list))
        self.assertIn('localhost', payload['data']['members'])

    def test_show_group_members_missing(self):
        """- attempt a show group members against a non-existent group"""
        response = self.app.get('api/v1/groups/walkabout',
                                headers=self.token_header())
        self.assertEqual(response.status_code,
                         404)

    def test_add_host_multiple_groups(self):
        """- add a host to multiple groups"""

        response = self.app.post('api/v1/groups/multi1',
                                 headers=self.token_header())
        self.assertEqual(response.status_code,
                         200)

        response = self.app.post('api/v1/groups/multi2',
                                 headers=self.token_header())
        self.assertEqual(response.status_code,
                         200)

        response = self.app.post('api/v1/groups/multi3',
                                 headers=self.token_header())
        self.assertEqual(response.status_code,
                         200)

        response = self.app.post('api/v1/hosts/localhost/groups/multi1?others=multi2,multi3', # noqa
                                 headers=self.token_header())
        self.assertEqual(response.status_code,
                         200)

    def test_hosts_with_invalid_parms(self):
        """- issue a host/group request with an invalid parameter"""
        response = self.app.post('api/v1/groups/parmcheck',
                                 headers=self.token_header())
        self.assertEqual(response.status_code,
                         200)
        response = self.app.post('api/v1/hosts/localhost/groups/parmcheck?myparm=dumb,dumber', # noqa
                                 headers=self.token_header())
        self.assertEqual(response.status_code,
                         400)

    def test_remove_host(self):
        """- remove a host from all groups"""
        response = self.app.post('api/v1/groups/removehost1',
                                 headers=self.token_header())
        self.assertEqual(response.status_code,
                         200)

        response = self.app.post('api/v1/groups/removehost2',
                                 headers=self.token_header())
        self.assertEqual(response.status_code,
                         200)

        response = self.app.post('api/v1/hosts/localhost/groups/removehost1?others=removehost2', # noqa
                                 headers=self.token_header())
        self.assertEqual(response.status_code,
                         200)

        response = self.app.delete('api/v1/hosts/localhost',
                                   headers=self.token_header())
        self.assertEqual(response.status_code,
                         200)

        root_dir = os.getcwd()
        inv_filename = os.path.join(root_dir, 'samples/inventory/hosts')
        inv_data = yaml.safe_load(fread(inv_filename))
        groups = inv_data['all']['children'].keys()
        for group in groups:
            hosts_in_group = inv_data['all']['children'][group]['hosts']
            if isinstance(hosts_in_group, dict):
                self.assertNotIn("localhost",
                                 hosts_in_group.keys())


if __name__ == "__main__":

    unittest.main(verbosity=2)
