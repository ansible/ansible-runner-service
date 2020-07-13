
import sys
import os
import json
import yaml
import unittest

sys.path.extend(["../", "./"])
from common import APITestCase, fake_ssh_client  # noqa
from runner_service.utils import fread      # noqa

class TestHostVars(APITestCase):

    def test_get_invalid_group(self):
        """- fetch hostsvars - nonexistent group"""
        response = self.app.get('api/v1/hostvars/bogus/groups/group1')

        self.assertEqual(response.status_code,
                         404)

    def test_get_invalid_host(self):
        """- fetch hostsvars - group valid, host invalid"""
        response = self.app.post('api/v1/groups/group2')
        self.assertEqual(response.status_code,
                         200)

        response = self.app.get('api/v1/hostvars/notallthere/groups/group2')

        self.assertEqual(response.status_code,
                         404)

    def test_add_hostvars_file(self):
        """- create hostvars, group doesn't need to exist"""
        payload = {"var1": "value1"}
        response = self.app.post('api/v1/hostvars/host1/groups/hosts',
                                 data=json.dumps(payload),
                                 content_type="application/json")
        self.assertEqual(response.status_code,
                         200)

    def test_add_hostvars_inventory_nogroup(self):
        """- create hostvars, but group doesn't exist"""
        payload = {"var1": "value1"}
        response = self.app.post('api/v1/hostvars/host1/groups/missing?type=inventory', # noqa E501
                                 data=json.dumps(payload),
                                 content_type="application/json")
        self.assertEqual(response.status_code,
                         404)

    def test_add_hostvars_inventory_nohost(self):
        """- create hostvars, inventory action - group OK, host NOTOK"""
        payload = {"var1": "value1"}
        response = self.app.post('api/v1/groups/hosts')
        self.assertEqual(response.status_code, 200)
        response = self.app.post('api/v1/hostvars/host1/groups/hosts?type=inventory', # noqa E501
                                 data=json.dumps(payload),
                                 content_type="application/json")
        self.assertEqual(response.status_code,
                         404)

    def test_add_hostvars_invalid_data(self):
        """- add hostvars, but data payload is invalid"""
        response = self.app.post('api/v1/groups/tahid')

        response = self.app.post('api/v1/hostvars/myhost/groups/tahid',
                                 data="invalid data",
                                 content_type="application/json")
        self.assertEqual(response.status_code,
                         400)

    def test_add_hostvars_request_invalid(self):
        """- add hostvars, but content-type not set"""
        response = self.app.post('api/v1/groups/tahri')
        payload = {"var1": "value1"}
        response = self.app.post('api/v1/hostvars/myhost/groups/tahri',
                                 data=json.dumps(payload),
                                 content_type="text/html")
        self.assertEqual(response.status_code,
                         415)
    @fake_ssh_client
    def test_add_hostvars_inventory(self):
        """- create hostvars (file), group and host valid"""
        response = self.app.post('api/v1/groups/tahi')
        self.assertEqual(response.status_code, 200)
        response = self.app.post('api/v1/hosts/localhost/groups/tahi')
        self.assertEqual(response.status_code, 200)

        payload = {"var1": "value1"}
        response = self.app.post('api/v1/hostvars/localhost/groups/tahi?type=inventory', # noqa E501
                                 data=json.dumps(payload),
                                 content_type="application/json")
        self.assertEqual(response.status_code,
                         200)
        cwd = os.getcwd()
        inv = yaml.safe_load(fread(os.path.join(cwd, 'samples/inventory/hosts'))) # noqa E501
        self.assertIn('var1', inv['all']['children']['tahi']['hosts']['localhost']) # noqa

    def test_fetch_hostvars_invalid(self):
        """- fetch hostsvars - no such host"""
        response = self.app.get('api/v1/hostvars/hosttfhi/groups/tfhi')
        self.assertEqual(response.status_code, 404)

    def test_fetch_hostvars(self):
        """- fetch hostvars"""
        response = self.app.post('api/v1/groups/tfh')
        self.assertEqual(response.status_code, 200)

        payload = {"var1": "value1"}
        response = self.app.post('api/v1/hostvars/tfhhost/groups/tfh',
                                 data=json.dumps(payload),
                                 content_type="application/json")
        self.assertEqual(response.status_code,
                         200)
        response = self.app.get('api/v1/hostvars/tfhhost/groups/tfh')
        self.assertEqual(response.status_code, 200)

    def test_delete_hostsvars_invalid(self):
        """- delete non-existent hostvars"""
        response = self.app.delete('api/v1/hostvars/deleteme/group/unknown')
        self.assertEqual(response.status_code, 404)

    @fake_ssh_client
    def test_delete_hostvars(self):
        """- delete valid hostvars (inventory or file removed)"""
        response = self.app.post('api/v1/groups/tdh')
        self.assertEqual(response.status_code, 200)
        response = self.app.post('api/v1/hosts/localhost/groups/tdh')
        self.assertEqual(response.status_code, 200)

        payload = {"var1": "value1"}
        response = self.app.post('api/v1/hostvars/localhost/groups/tdh',
                                 data=json.dumps(payload),
                                 content_type="application/json")
        self.assertEqual(response.status_code, 200)

        response = self.app.delete('api/v1/hostvars/localhost/groups/tdh')
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":

    unittest.main(verbosity=2)
