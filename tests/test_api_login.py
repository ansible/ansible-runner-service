
import sys
import logging
import requests
import unittest

sys.path.extend(["../", "./"])
from common import APITestCase  # noqa


# turn of normal logging that the ansible_runner_service will generate
nh = logging.NullHandler()
r = logging.getLogger()
r.addHandler(nh)


class TestLogin(APITestCase):

    def test_good_login(self):
        """- test happy state login"""
        url = "https://localhost:{}/api/v1/login".format(self.config.port)
        response = requests.get(url,
                                auth=('admin', 'admin'),
                                verify=False)
        self.assertEqual(response.status_code,
                         200)
        self.assertIn('token', response.json()['data'])

    def test_bad_password(self):
        """- test bad password"""
        url = "https://localhost:{}/api/v1/login".format(self.config.port)
        response = requests.get(url,
                                auth=('admin', 'wah'),
                                verify=False)
        self.assertEqual(response.status_code,
                         401)
        self.assertIn('password incorrect', response.json()['msg'])

    def test_bad_user(self):
        """- test bad username"""
        url = "https://localhost:{}/api/v1/login".format(self.config.port)
        response = requests.get(url,
                                auth=('wee', 'wah'),
                                verify=False)
        self.assertEqual(response.status_code,
                         401)
        self.assertIn('unknown user', response.json()['msg'])

    def test_access_without_token(self):
        """- test access to a protected endpoint, without token"""
        url = "https://localhost:{}/api/v1/groups".format(self.config.port)
        response = requests.get(url,
                                verify=False)
        self.assertEqual(response.status_code,
                         401)


if __name__ == "__main__":

    unittest.main(verbosity=2)
