# ansible-runner-service    ![Build status](https://travis-ci.com/pcuzner/ansible-runner-service.svg?branch=master)
This is a POC project which wraps the ansible_runner interface inside a REST API.  

The incentive for this is two-fold;
- provide Ansible integration to non-python projects
- provide a means of programmatically running playbooks where the ansible engine is running on a separate host or in a separate container

## Prerequisites
So far I've just been testing against Fedora28 - other distros may use older
versions of packages like flask that may not work correctly.

### Package Dependencies
- Python 3.6
- pyOpenSSL  (python3-pyOpenSSL on Fedora, CentOS pyOpenSSL)
- ansible_runner 1.0.5 or above  

*if in doubt, look in the misc/docker folder and build the container!*

## Installation
Try before you buy...simply unzip the archive and run :)
```
python3 ansible_runner_service.py
```
This is 'dev' mode - all files and paths are relative to the path that you've
unzipped the project into.

For 'prod' mode, a setup.py is provided. Once the package is installed and
called from /usr/bin, the script will expect config and output files to be
found in all normal locations (see proposed file layout below)  
```
sudo python3 setup.py install --record installed_files --single-version-externally-managed
```

Once this is installed, you may start the service with
```
ansible_runner_service
```
Word of warning though ... 'prod' mode is less tested!

## API Endpoints

Once the service is running, you can point your browser at  ```https://localhost:5001/api``` to show which endpoints are available. Each endpoint is described along with a curl example showing invocation and output.  

![API endpoints](./screenshots/runner-service-api.gif)

You may click on any row to expand the description of the API route and show the curl example. The app uses a self-signed certificate, so all examples use the -k parameter (insecure mode).  

**Note**: *It is not the intent of this API to validate the parameters passed to it. It is assumed that parameter selection and validation happen prior to the API call.*  

Here's a quick 'cheat sheet' of the API endpoints.  

| API Route | Description |
|-----------|-------------|
|/api | Show available API endpoints (this page)|
|/api/v1/groups| List all the defined groups in the inventory|
|/api/v1/groups/<group_name>| Manage groups within the inventory|
|/api/v1/hosts| Return a list of hosts from the inventory|
|/api/v1/hosts/<host_name>| Show group membership for a given host|
|/api/v1/hosts/<host_name>/groups/<group_name>| Manage ansible control of a given host|
|/api/v1/jobs/<play_uuid>/events| Return a list of events within a given playbook run (job)|
|/api/v1/jobs/<play_uuid>/events/<event_uuid>| Return the output of a specific task within a playbook|
|/api/v1/login| Authenticate user and provide token|
|/api/v1/playbooks| Return the names of all available playbooks|
|/api/v1/playbooks/<play_uuid>| Query the state or cancel a playbook run (by uuid)|
|/api/v1/playbooks/<playbook_name>| Start a playbook by name, returning the play's uuid|
|/api/v1/playbooks/<playbook_name>/tags/<tags>| Start a playbook using tags to control which tasks run|
|/metrics| Provide prometheus compatible statistics which describe playbook [activity](./misc/dashboards/README.md) |


## Testing
Testing to date has all been lab based i.e. please **do not use in production** environments. Playbook integration with Ceph and Gluster has been the primary focus together with the probe-disks.yml playbook. Did you spot the theme?..*It's all about the storage™ :)*  

For example, with ceph the ```osd-configure.yml``` playbook has been tested successfully.

### Manual Testing
The archive, downloaded from github, contains a simple playbook that just uses the bash sleep command - enabling you to quickly experiment with the API.

Use the steps below (dev mode), to quickly exercise the API  
1. Authenticate user and provide token
```curl -k -i --user admin:admin https://localhost:5001/api/v1/login -X get```
2. Get the list of available playbooks (should just be test.yml)  
```curl -k -i -H "Authorization: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE1MzczODA3MTR9.CbTXvBum5mCq9s56wJNiMn8JLJ0UzzRdwdeOFctJtbI" https://localhost:5001/api/v1/playbooks  -X GET```
3. Run the test.yml playbook, passing the time_delay parameter (30 secs should be enough).  
```curl -k -i -H "Authorization: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE1MzczODA3MTR9.CbTXvBum5mCq9s56wJNiMn8JLJ0UzzRdwdeOFctJtbI" -H "Content-Type: application/json" --data '{"time_delay": 30}' https://localhost:5001/api/v1/playbooks/test.yml -X POST```  
4. The previous command will return the playbooks UUID. Use this identifier to query the state or progress of the run.  
```curl -k -i -H "Authorization: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE1MzczODA3MTR9.CbTXvBum5mCq9s56wJNiMn8JLJ0UzzRdwdeOFctJtbI" https://localhost:5001/api/v1/playbooks/f39069aa-9f3d-11e8-852f-c85b7671906d -X GET```
5. Get a list of all the events in a playbook. The return list consists of all the job event ID's  
```curl -k -i -H "Authorization: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE1MzczODA3MTR9.CbTXvBum5mCq9s56wJNiMn8JLJ0UzzRdwdeOFctJtbI" https://localhost:5001/api/v1/jobs/f39069aa-9f3d-11e8-852f-c85b7671906d/events  -X GET```
6. To get specific output from a job event, you can query the job event  
```curl -k -i -H "Authorization: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE1MzczODA3MTR9.CbTXvBum5mCq9s56wJNiMn8JLJ0UzzRdwdeOFctJtbI" https://localhost:5001/api/v1/jobs/f39069aa-9f3d-11e8-852f-c85b7671906d/events/13-c85b7671-906d-e52d-d421-000000000008  -X GET```  

Obviously you'll need to change the play and job uuids for your run :)

## Usage and Workflows
< INSERT WARP DRIVE HERE >

## Regression Testing
< INSERT HYPERDRIVE HERE >

## File Layout (Proposed)

/etc/ansible-runner-service
- logging.yaml  
- config.yaml  
- ansible-runner-service.crt  
- ansible-runner-service.key  

/usr/share/ansible-runner-service  
- artifacts  
- inventory  
- env  
- project
    -  roles (optional)
    -  library (optional)
    -  test.yaml  
- roles

/var/log/ansible-runner-service.log  

/usr/share/doc/ansible-runner-service  
- README.md  
- LICENSE.md  

/etc/systemd/system  
- ansible-runner-service.service  

/usr/bin/ or /usr/local/bin    
- ansible_runner_service  
