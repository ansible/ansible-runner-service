import os
import sys
import json
from base64 import b64encode
import shutil

import unittest

sys.path.extend(["../", "./"])
from ansible_runner_service import main     # noqa E402
from runner_service import configuration    # noqa


def setup_dirs(dir_list=[]):
    """Create the sample directory structure for the API to work against"""
    root_dir = os.getcwd()
    samples = os.path.join(root_dir, 'samples')

    if os.path.exists(samples):
        shutil.rmtree(samples)

    os.mkdir(samples)

    for _d in dir_list:
        new_dir = os.path.join(samples, _d)
        os.mkdir(new_dir)


def seed_dirs(seed_list):

    for seed_pair in seed_list:
        src, dest = seed_pair
        if os.path.isdir(src):
            shutil.copytree(src, dest)
        else:
            shutil.copyfile(src, dest)


def get_auth_header(username, password):

    auth = "{}:{}".format(username, password)
    encoded_credentials = b64encode(auth.encode())

    # account for differences in python2 and python3 encoding
    if isinstance(encoded_credentials, bytes):
        encoded_credentials = encoded_credentials.decode('ascii')

    return {'Authorization': 'Basic ' + encoded_credentials}  # noqa


class APITestCase(unittest.TestCase):
    app = None
    token = None

    def token_header(self):
        return {'Authorization': self.token}

    def auth_header(self, username, password):
        return get_auth_header(username, password)

    @classmethod
    def setUpClass(cls):
        """
        Call the main method of the ansible_runner_service script to Start
        the daemon normally
        """

        setup_dirs([
            'env',
            'inventory',
            'project',
            'artifacts'
            ])

        seed_dirs([
            ('./data/artifacts/53b955f2-b79a-11e8-8be9-c85b7671906d',
             './samples/artifacts/53b955f2-b79a-11e8-8be9-c85b7671906d'),
            ('./data/project/testplaybook.yml',
             './samples/project/testplaybook.yml')
            ])

        configuration.init("dev")
        cls.config = configuration.settings
        cls.app = main(test_mode=True)
        response = cls.app.get('/api/v1/login',
                               headers=get_auth_header('admin', 'admin'))

        assert response.status_code == 200, "Unable to get login token"

        cls.token = json.loads(response.data).get('data')['token']

    @classmethod
    def get_token(cls):
        response = APITestCase.app.get('/api/v1/login',
                                       headers=get_auth_header('admin', 'admin'))   # noqa

        assert response.status_code == 200, "Unable to get login token"

        response_data = json.loads(response.data)
        return response_data.get('data')['token']

    @classmethod
    def tearDownClass(cls):
        root_dir = os.getcwd()
        samples = os.path.join(root_dir, 'samples')
        shutil.rmtree(samples)
