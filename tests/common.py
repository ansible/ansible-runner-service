import os
import time
import shutil
import socket
import urllib3
import unittest
import requests
from multiprocessing import Process

from ansible_runner_service import *        # noqa
from runner_service import configuration    # noqa


def setup_dirs(dir_list=[]):
    """Create the sample directory structure for the daemon to work within"""
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


def wait_for_api(port_num=5001):
    """Attempt a socket connect on a given port, wait until connect succeeds"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        result = sock.connect_ex(('127.0.0.1', port_num))
        if result == 0:
            break
        time.sleep(0.1)
    sock.close()


def tcp_port_free(port_num=5001):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        result = sock.connect_ex(('127.0.0.1', port_num))
    except Exception as err:
        raise
    finally:
        sock.close()

    return False if result == 0 else True


class APITestCase(unittest.TestCase):
    server = None
    config = None
    token = None

    @classmethod
    def setUpClass(cls):
        """
        Call the main method of the ansible_runner_service script to Start
        the daemon normally
        """

        # Need to handle the disable here to get rid of the urllib3
        # InsecureRequestWarning messages due to our self signed certs
        # i.e. InsecureRequestWarning: Unverified HTTPS request is being made.
        urllib3.disable_warnings()

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

        # wait for port to be free to bind to, incase multiple instances run
        # concurrently
        while True:
            if tcp_port_free(port_num=configuration.settings.port):
                break
            time.sleep(0.1)

        # Now the port is free, we can start the server by pushing the api
        # server into it's own process, so we can kill it! Each testcase will
        # create a fresh API server environment so by using a process model
        # we can kill the api server, and clean up ready for the next testcase
        cls.server = Process(target=main,)                 # noqa
        cls.server.daemon = True
        cls.server.start()

        wait_for_api(port_num=configuration.settings.port)

        cls.token = APITestCase.get_token()

    @classmethod
    def get_token(cls):
        response = requests.get("https://localhost:{}/api/v1/login".format(configuration.settings.port), # noqa
                                auth=('admin',
                                configuration.settings.passwords['admin']),
                                verify=False)
        assert response.status_code == 200, "Unable to get login token"
        cls.token = response.json()['data']['token']

    @classmethod
    def tearDownClass(cls):
        cls.server.terminate()
        cls.server.join()

        root_dir = os.getcwd()
        samples = os.path.join(root_dir, 'samples')
        shutil.rmtree(samples)

    def get(self, endpoint, auth=None):
        url = "https://localhost:{}/api/v1{}".format(configuration.settings.port,      # noqa
                                                      endpoint)
        parms = {
            "url": url,
            "headers": {"Authorization": APITestCase.token},
            "verify": False
        }

        if auth:
            parms['auth'] = auth

        return requests.get(**parms)

    def post(self, endpoint, payload=None):
        url = "https://localhost:{}/api/v1{}".format(configuration.settings.port,      # noqa
                                                     endpoint)
        parms = {
            "url": url,
            "headers": {"Authorization": APITestCase.token},
            "verify": False
        }

        if isinstance(payload, dict):
            parms['json'] = payload

        return requests.post(**parms)

    def delete(self, endpoint):
        url = "https://localhost:{}/api/v1{}".format(configuration.settings.port,      # noqa
                                                     endpoint)
        parms = {
            "url": url,
            "headers": {"Authorization": APITestCase.token},
            "verify": False
        }

        return requests.delete(**parms)
