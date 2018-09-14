
import os
import sys
import time
import shutil
import socket
import logging
import urllib3
import requests
import unittest
import threading

sys.path.append("../")

from ansible_runner_service import *        # noqa
from runner_service import configuration    # noqa

# turn of normal logging that the ansible_runner_service will generate
nh = logging.NullHandler()
r = logging.getLogger()
r.addHandler(nh)


def setup_dirs(dir_list=[]):
    """Create the sample directory structure for the daemon to work within"""
    root_dir = os.getcwd()
    samples = os.path.join(root_dir, 'samples')
    try:
        shutil.rmtree(samples)
    except FileNotFoundError:
        pass
    finally:
        os.mkdir(samples)

    for _d in dir_list:
        new_dir = os.path.join(samples, _d)
        os.mkdir(new_dir)


def wait_for_api(port_num=5001):
    """Attempt a socket connect on a given port, wait until connect succeeds"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        result = sock.connect_ex(('127.0.0.1', port_num))
        if result == 0:
            break
        time.sleep(0.1)
    sock.close()


class TestAPI(unittest.TestCase):

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
            ])

        configuration.init("dev")
        _t = threading.Thread(target=main, )    # noqa
        _t.daemon = True
        _t.start()

        wait_for_api()

    @classmethod
    def tearDownClass(cls):
        root_dir = os.getcwd()
        samples = os.path.join(root_dir, 'samples')
        shutil.rmtree(samples)

    def test_api(self):
        """Test the API endpoint '/api' responds"""

        response = requests.get("https://localhost:5001/api", verify=False)

        self.assertEqual(response.status_code,
                         200)
        self.assertEqual(response.headers['Content-Type'],
                         'text/html; charset=utf-8')


if __name__ == "__main__":

    unittest.main(verbosity=2)
