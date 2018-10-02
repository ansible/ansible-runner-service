
import sys
import json
import logging

import unittest

sys.path.extend(["../", "./"])
from common import APITestCase  # noqa
from ansible_runner_service import main     # noqa E402

# turn of normal logging that the ansible_runner_service will generate
nh = logging.NullHandler()
r = logging.getLogger()
r.addHandler(nh)


class TestLogin(APITestCase):

    def test_good_login(self):
        """- test happy state login"""

        response = self.app.get('/api/v1/login',
                                headers=self.auth_header('admin', 'admin'))
        self.assertEqual(response.status_code,
                         200)
        self.assertIn('token', json.loads(response.data)['data'])

    def test_bad_password(self):
        """- test bad password"""

        response = self.app.get('/api/v1/login',
                                headers=self.auth_header('admin', 'wah'))

        self.assertEqual(response.status_code,
                         401)
        self.assertIn('password incorrect', json.loads(response.data)['msg'])

    def test_bad_user(self):
        """- test bad username"""

        response = self.app.get('/api/v1/login',
                                headers=self.auth_header('wee', 'wah'))

        self.assertEqual(response.status_code,
                         401)
        self.assertIn('unknown user', json.loads(response.data)['msg'])

    def test_login_no_credentials(self):
        """- test login without a username/password header"""
        response = self.app.get('/api/v1/login')

        self.assertEqual(response.status_code,
                         401)

    def test_access_without_token(self):
        """- test access to a protected endpoint, without token"""

        response = self.app.get('/api/v1/groups')

        self.assertEqual(response.status_code,
                         401)

    def test_access_with_bad_token(self):
        """- test access with an unknown token"""
        invalid_token = self.token_header()["Authorization"][::-1]  # reverse

        response = self.app.get('/api/v1/groups',
                                headers={"Authorization": invalid_token})
        self.assertEqual(response.status_code,
                         401)


if __name__ == "__main__":

    unittest.main(verbosity=2)
