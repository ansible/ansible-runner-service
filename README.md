# ansible-runner-service  
This project wraps the ansible_runner interface inside a REST API enabling ansible playbooks to be executed and queried from other platforms.

The incentive for this is two-fold;
- provide Ansible integration to non-python projects
- provide a means of programmatically running playbooks where the ansible engine is running on a separate host or in a separate container

## Features
The core of this project is ansible_runner, so first of all, a quick call out to those [folks](https://github.com/ansible/ansible-runner/graphs/contributors) for such an awesome tool!
#### Security
- https support (http not supported)
  - production version:
    - uses TLS mutual authentication. (<misc/nginx> folder provides a container to be used in production)
    - Valid client and server certificates must be used to access the API (See documentation in <misc/nginx> folder)
  - test version:
    - uses self-signed if existing crt/key files are not present (<misc/docker> provides a container to be used in test systems)
    - if not present, generates self-signed on first start up
- creates or reuses ssh pub/priv keys for communication with target hosts

#### Monitoring
  - /metrics endpoint provides key metrics for monitoring the instance with [Prometheus](https://prometheus.io/)
  - a sample [Grafana](https://grafana.com/) dashboard is provided in the ```misc/dashboards``` directory to track activity

#### Playbook Execution
  - exposes playbooks by name found within the project folder
  - supports Ansible environments that use private libraries (ie. the library directory is stored within the project folder)
  - playbooks can be run with tags to change execution behavior
  - playbooks can use limit to restrict actions to a specific host
  - playbooks can use `check` parameter to run the `ansible-runner` in check mode
  - running playbooks may be cancelled
  - supports execution of concurrent playbooks

#### Playbook State
  - playbook state and output can be queried during and after execution
  - playbook state shows overall status, with current active task name
  - the caller can request all events associated with current or past playbook runs
  - events may be filtered for specific output e.g. ?task=RSEULTS to show events with a taskname of RESULTS
  - playbook state is cached to improve API response times

#### Inventory management
  - hosts and ansible groups are managed through the API ```/groups``` and ```/hosts``` endpoints
  - Before a host can be added to the inventory, it is checked for dns, and passwordless ssh
  - missing public keys on 'candidate' hosts, result in the instance's public key being returned to the caller. The requester can then arrange for this key to be installed on the candidate host.
  - host and group vars supported either inside the 'hosts' file, or in the host_vars/group_vars sub-directories


#### Developer Friendly
  - simple to use REST API allowing playbooks to be run, and results/state queried
  - provides a ```/api``` endpoint describing each endpoint
  - ```/api``` content is automatically generated and has no external dependencies
  - each description includes an curl command example, together with output

#### Deployment
  - supports docker - Dockerfile and README included
  - cross platform support (docker image uses CentOS7 base, build process executes against Ubuntu)
  - can be packaged as an rpm or run as a container
  - designed to offer core ansible functionality, supplemented by a users set of playbooks/roles/library
  - supports configuration options through a specific /etc directory
  - configuration options may be overridden at the command line for diagnostics
  - all relevant activity is logged


## Prerequisites
So far, testing has been mainly against Fedora (28) and the CentOS7 for the docker image. Other distros may work fine (Travis build uses Ubuntu Trusty for example!).

### Package Dependencies
- Python 3.6
- pyOpenSSL  (python3-pyOpenSSL on Fedora, CentOS pyOpenSSL)
- ansible_runner 1.1.1 or above

(see ```requirements.txt``` for a more complete list of the python dependencies)

*if in doubt, look in the <misc/docker> folder and build the container!*

## Installation
Try before you buy...assuming you have an environment that meets the python3 dependencies, simply unzip the archive and run :)
```
python3 ansible_runner_service.py
```
When you run from any directory outside of /usr, the script regards this as 'dev' mode. In this mode, all files and paths are relative to the path that you've
unzipped the project into.

For 'prod' mode, a setup.py is provided. Once the package is installed and
called from /usr/*/bin, the script will expect config and output files to be
found in all the normal 'production' locations (see proposed file layout below)
```
sudo python3 setup.py install --record installed_files --single-version-externally-managed
```

Once this is installed, you may start the service with
```
ansible_runner_service
```
## Production ready container

A container suitable for production systems can be build using the 'Dockerfile' present in the project root folder. It uses nginx with mutual TLS authentication to provide the Ansible Runner Service API.

Check documentation in <misc/nginx/README.md> folder for more information.

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
|/api/v1/groupvars/<group_name>| Manage group variables|
|/api/v1/hosts| Return a list of hosts from the inventory|
|/api/v1/hosts/<host_name>| Show group membership for a given host|
|/api/v1/hosts/<host_name>/groups/<group_name>| Manage ansible control of a given host|
|/api/v1/hostvars/<host_name>/groups/<group_name>| Manage host variables for a specific group within the inventory|
|/api/v1/jobs/<play_uuid>/events| Return a list of events within a given playbook run (job)|
|/api/v1/jobs/<play_uuid>/events/<event_uuid>| Return the output of a specific task within a playbook|
|/api/v1/playbooks| Return the names of all available playbooks|
|/api/v1/playbooks/<play_uuid>| Query the state or cancel a playbook run (by uuid)|
|/api/v1/playbooks/<playbook_name>| Start a playbook by name, returning the play's uuid|
|/api/v1/playbooks/<playbook_name>/tags/<tags>| Start a playbook using tags to control which tasks run|
|/metrics| Provide prometheus compatible statistics which describe playbook [activity](./misc/dashboards/README.md) |


## Testing
Testing to date has all been lab based, so please bear this in mind if considering using this tool for production use cases (*bug reports welcome!*). Playbook integration with Ceph and Gluster has been the primary focus together with the probe-disks.yml playbook. Did you spot the theme?..*It's all about the storage™ :)*

For example, with ceph the ```osd-configure.yml``` playbook has been tested successfully.

### Manual Testing
The archive, downloaded from github, contains a simple playbook that just uses the bash sleep command - enabling you to quickly experiment with the API.

Use the steps below (test mode/test container version <misc/docker>), to quickly exercise the API
1. Get the list of available playbooks (should just be test.yml)
```curl -k -i https://localhost:5001/api/v1/playbooks  -X GET```
2. Run the runnertest.yml playbook, passing the time_delay parameter (30 secs should be enough).
```curl -k -i -H "Content-Type: application/json" --data '{"time_delay": 30}' https://localhost:5001/api/v1/playbooks/runnertest.yml -X POST```
4. The previous command will return the playbooks UUID. Use this identifier to query the state or progress of the run.
```curl -k -i https://localhost:5001/api/v1/playbooks/f39069aa-9f3d-11e8-852f-c85b7671906d -X GET```
5. Get a list of all the events in a playbook. The return list consists of all the job event ID's
```curl -k -i https://localhost:5001/api/v1/jobs/f39069aa-9f3d-11e8-852f-c85b7671906d/events  -X GET```
6. To get specific output from a job event, you can query the job event
```curl -k -i https://localhost:5001/api/v1/jobs/f39069aa-9f3d-11e8-852f-c85b7671906d/events/13-c85b7671-906d-e52d-d421-000000000008  -X GET```

Obviously you'll need to change the playbook uuid and job uuids for your run :)

## Tips & Tricks
1. Tweaking the environment:The script uses a configuration module which is accessible across the different modules within the project. There are two ways that settings in the configuration module can be overridden;
    - by using a ```config.yaml``` file
    - by providing a setting value when starting the ansible_runner_service program

2. Overriding configuration at run time, lets you do quick tests like this;

    - start the service, but don't perform any passwordless ssh tests
    ```
    $ ssh_checks=false python3 ansible_runner_service
    ```
    - change the target user when validating ssh connection is in place
    ```
    $ target_user=root python3 ansible_runner_service
    ```


## Automated Build & Testing
The project uses Travis CI integration to check the following;
- Installation
- code style (using flake8)
- Ansible inventory management (groups/hosts)
- API endpoints using test data and a test playbook

For more info, look at the ```.travis.yml``` file.


## File Layout (Proposed)

/etc/ansible-runner-service
- logging.yaml
- config.yaml
- ansible-runner-service.crt (used only with the development Flask server)
- ansible-runner-service.key (used only with the development Flask server)
- certs
    -  client (optional placement for store authorized client certificates)
    -  server
         -  server.crt (server certificate issued by <ca>)
         -  server.key (server certificate key)
         -  ca.crt     (certificate authority cert to validate client certificates)
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
