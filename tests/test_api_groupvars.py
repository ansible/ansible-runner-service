
import sys
import os
import json
import yaml
import unittest

sys.path.extend(["../", "./"])
from common import APITestCase  # noqa
from runner_service.utils import fread      # noqa


class TestGroupVars(APITestCase):

    def test_list_invalid_groupvars(self):
        """- list groupvars for a non-existent group"""
        response = self.app.get('api/v1/groupvars/wobbles')

        self.assertEqual(response.status_code,
                         404)

    def test_add_invalid_groupvars(self):
        """ - create group vars for non-existent group"""

        payload = {"var1": "value1"}
        response = self.app.post('api/v1/groupsvars/gv1',
                                 data=json.dumps(payload),
                                 content_type="application/json")
        self.assertEqual(response.status_code,
                         404)

    def test_add_invalid_payload(self):
        """ - create group vars with non json data"""
        response = self.app.post('api/v1/groups/gv2')

        response = self.app.post('api/v1/groupvars/gv2',
                                 data="invalid data",
                                 content_type="application/json")
        self.assertEqual(response.status_code,
                         400)

    def test_add_invalid_content(self):
        """ - create group vars but without json contenttype"""
        response = self.app.post('api/v1/groups/gv3')
        payload = {"var1": "value1"}
        response = self.app.post('api/v1/groupvars/gv3',
                                 data=json.dumps(payload),
                                 content_type="text/html")
        self.assertEqual(response.status_code,
                         415)

    def test_delete_invalid_groupvars(self):
        """ - attempt to delete a non-existent groupvars entry"""
        response = self.app.delete("api/v1/groupvars/gv1")
        self.assertEqual(response.status_code,
                         404)

    def test_add_groupvars_file(self):
        """ - add a group and groupvars (file)"""
        payload = {"var1": "value1"}

        response = self.app.post('api/v1/groups/gvadd')
        response = self.app.post('api/v1/groupvars/gvadd',
                                 data=json.dumps(payload),
                                 content_type="application/json")
        self.assertEqual(response.status_code,
                         200)
        cwd = os.getcwd()
        self.assertTrue(os.path.exists(
                          os.path.join(cwd,
                                       'samples/project/group_vars/gvadd.yml'))) # noqa E501

    def test_add_groupvars_inventory(self):
        """ - add a group and groupvars (inventory - hosts)"""
        payload = {"var1": "value1"}

        response = self.app.post('api/v1/groups/gvaddinv')
        response = self.app.post('api/v1/groupvars/gvaddinv?type=inventory',
                                 data=json.dumps(payload),
                                 content_type="application/json")
        self.assertEqual(response.status_code,
                         200)
        cwd = os.getcwd()
        inv = yaml.safe_load(fread(os.path.join(cwd, 'samples/inventory/hosts'))) # noqa E501
        self.assertIn('var1', inv['all']['children']['gvaddinv']['vars'])

    def test_fetch_groupvars(self):
        """- fetch group vars"""
        payload = {"var1": "value1"}
        response = self.app.post('api/v1/groups/fetchvars')
        self.assertEqual(response.status_code, 200)
        response = self.app.post('api/v1/groupvars/fetchvars',
                                 data=json.dumps(payload),
                                 content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response = self.app.get('api/v1/groupvars/fetchvars')
        self.assertEqual(response.status_code, 200)

        payload = json.loads(response.data)
        self.assertIn('var1', payload['data']['vars'].keys())

    def test_delete_groupvars_file(self):
        """- delete groupvars (from group_vars dir)"""
        payload = {"var1": "value1"}
        response = self.app.post("api/v1/groups/gvdel")
        self.assertEqual(response.status_code, 200)
        response = self.app.post('api/v1/groupvars/gvdel',
                                 data=json.dumps(payload),
                                 content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response = self.app.delete('api/v1/groupvars/gvdel')
        self.assertEqual(response.status_code, 200)
        cwd = os.getcwd()
        gvars_files = os.listdir(os.path.join(cwd, 'samples/project/group_vars')) # noqa E501
        self.assertNotIn('gvdel', gvars_files)

    def test_delete_groupvars_inv(self):
        """- delete groupvars (from group_vars dir)"""
        payload = {"var1": "value1"}
        response = self.app.post("api/v1/groups/gvinventory")
        self.assertEqual(response.status_code, 200)
        response = self.app.post('api/v1/groupvars/gvinventory?type=inventory',
                                 data=json.dumps(payload),
                                 content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response = self.app.delete('api/v1/groupvars/gvinventory')
        self.assertEqual(response.status_code, 200)

        cwd = os.getcwd()
        inv = yaml.safe_load(fread(os.path.join(cwd, 'samples/inventory/hosts'))) # noqa E501
        self.assertNotIn('vars', inv['all']['children']['gvinventory'])


if __name__ == "__main__":

    unittest.main(verbosity=2)
