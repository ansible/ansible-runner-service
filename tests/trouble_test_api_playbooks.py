import sys
import json
import time
import logging
import unittest

sys.path.extend(["../", "./"])
from common import APITestCase                # noqa

# turn of normal logging that the ansible_runner_service will generate
nh = logging.NullHandler()
r = logging.getLogger()
r.addHandler(nh)


# TODO: Getting Playbok status does not work ... problem/bug in "ansible runner"
"""
        ------------- Trying to get the playbook status request produces this error ---------------------------
        ex: response = self.app.get('api/v1/playbooks/{}'.format(play_uuid))
        -------------------------------------------------------------------------------------------------------

        2019-03-22 10:20:09,762 - runner_service.controllers.playbooks - INFO - Playbook testplaybook.yml, UUID=b0874eb4-4c83-11e9-b0dc-2016b900e38f initiated : status=starting

        2019-03-22 10:20:09,764 - runner_service.controllers.playbooks - DEBUG - Request received, content-type :None
        2019-03-22 10:20:09,764 - runner_service.controllers.playbooks - INFO - 127.0.0.1 - GET /api/v1/playbooks/b0874eb4-4c83-11e9-b0dc-2016b900e38f
        2019-03-22 10:20:09,764 - runner_service.services.playbook - DEBUG - runner_cache 'hit' for playbook status request
        /home/jolmomar/Code/ansible-runner-service/.tox/py36/lib/python3.6/site-packages/ansible_runner/utils.py:321: ResourceWarning: unclosed file <_io.BufferedWriter name='/home/jolmomar/Code/ansible-runner-service/samples/artifacts/b0874eb4-4c83-11e9-b0dc-2016b900e38f/ssh_key_data'>
          threading.Thread(target=lambda p, d: open(p, 'wb').write(d),
        2019-03-22 10:20:10,267 - runner_service.controllers.playbooks - DEBUG - Request received, content-type :None
        2019-03-22 10:20:10,267 - runner_service.controllers.playbooks - INFO - 127.0.0.1 - GET /api/v1/playbooks/b0874eb4-4c83-11e9-b0dc-2016b900e38f
        2019-03-22 10:20:10,267 - runner_service.services.playbook - DEBUG - runner_cache 'hit' for playbook status request
        Exception in thread Thread-50:
        Traceback (most recent call last):
        File "/usr/lib64/python3.6/threading.py", line 916, in _bootstrap_inner
            self.run()
        File "/usr/lib64/python3.6/threading.py", line 864, in run
            self._target(*self._args, **self._kwargs)
        File "/home/jolmomar/Code/ansible-runner-service/.tox/py36/lib/python3.6/site-packages/ansible_runner/runner.py", line 165, in run
            stdout_handle.close()
        File "/home/jolmomar/Code/ansible-runner-service/.tox/py36/lib/python3.6/site-packages/ansible_runner/utils.py", line 280, in close
            self._emit_event(value)
        File "/home/jolmomar/Code/ansible-runner-service/.tox/py36/lib/python3.6/site-packages/ansible_runner/utils.py", line 307, in _emit_event
            self._event_callback(event_data)
        File "/home/jolmomar/Code/ansible-runner-service/.tox/py36/lib/python3.6/site-packages/ansible_runner/runner.py", line 65, in event_callback
            should_write = self.event_handler(event_data)
        File "/home/jolmomar/Code/ansible-runner-service/runner_service/services/playbook.py", line 160, in cb_event_handler
            runner_cache[ident]['role'] = event_data['event_data'].get('role', '')
        KeyError: 'event_data'

"""


class TestPlaybooks(APITestCase):

    def test_run_playbook(self):
        """- start a playbook"""
        # create a playbook group and put localhost in it
        """- Add a host to a group - 404 unless ssh_checks turned off"""

        response = self.app.post('api/v1/groups/playbook')

        self.assertEqual(response.status_code,
                         200)

        response = self.app.post('api/v1/hosts/localhost/groups/playbook')
        self.assertEqual(response.status_code,
                         200)

        response = self.app.post('api/v1/playbooks/testplaybook.yml',
                                 data=json.dumps(dict()),
                                 content_type="application/json")
        self.assertEqual(response.status_code,
                         202)     # it started OK

        play_uuid = json.loads(response.data)['data']['play_uuid']

        # wait for playbook completion
        while True:
            response = self.app.get('api/v1/playbooks/{}'.format(play_uuid))

            self.assertIn(response.status_code, [200, 404])

            if json.loads(response.data)['msg'] in ['failed', 'successful']:
                break
            time.sleep(0.5)

    def test_run_playbook_tags(self):
        """- run a playbook using tags"""


        self.assertTrue(True)


        response = self.app.post('api/v1/playbooks/testplaybook.yml/tags/solo',
                                 data=json.dumps(dict()),
                                 content_type="application/json")
        self.assertEqual(response.status_code,
                         202)     # it started OK

        play_uuid = json.loads(response.data)['data']['play_uuid']

        # wait for playbook completion
        while True:
            response = self.app.get('api/v1/playbooks/{}'.format(play_uuid))

            self.assertIn(response.status_code, [200, 404])
            if json.loads(response.data)['msg'] in ['successful', 'failed']:
                break
            time.sleep(0.5)


    def test_run_playbook_limited(self):
        """- run a playbook that uses limit"""

        response = self.app.post('api/v1/playbooks/testplaybook.yml?limit=localhost',   # noqa
                                 data=json.dumps(dict()),
                                 content_type="application/json")
        self.assertEqual(response.status_code,
                         202)     # it started OK

        play_uuid = json.loads(response.data)['data']['play_uuid']
        # wait for playbook completion

        while True:
            response = self.app.get('api/v1/playbooks/{}'.format(play_uuid))

            self.assertIn(response.status_code, [200, 404])
            if json.loads(response.data)['msg'] in ['successful', 'failed']:
                break

            time.sleep(0.5)

    def test_cancel_running_playbook(self):
        """- Issue a cancel against a running playbook"""

        response = self.app.post('api/v1/playbooks/testplaybook.yml',
                                 data=json.dumps(dict()),
                                 content_type="application/json")
        self.assertEqual(response.status_code,
                         202)     # it started OK

        play_uuid = json.loads(response.data)['data']['play_uuid']
        response = self.app.delete('api/v1/playbooks/{}'.format(play_uuid))
        self.assertEqual(response.status_code,
                         200)
