# Running ansible-runner-service in a container

## WARNING: THIS IS A WORK IN PROGRESS!

## Goal:
Provide a container version of the ansible runner service running in 'prod' mode

The container runs ansible runner service with bind mounts out to the local filesystem
to provide runtime, playbooks and artifacts persistence. This approach allows you to
install an rpm containing the playbooks specific to ceph or gluster, then map these
through to the Container.

The provided container uses CentOS with Python 3.6 (most of the development work is being done against Fedora, with Python3.6).


## Local Preparation
1. download the project to your home directory and untar/unzip
2. create an archive of the project called ansible-runner-service.tar.gz and
store it in the misc/docker directory
3. set up you local environment to persist the config
```
 sudo mkdir /etc/ansible-runner-service
 sudo mkdir -p /usr/share/ansible-runner-service/{artifacts,env,inventory, project}
```
3.a. If you have selinux enabled you'll need to give the container permissions to these directories  
```
cd /usr/share
chcon -Rt container_file_t ansible-runner-service
```
4. from the root of the ansible-runner-service directory
```
 cp {logging,config}.yaml /etc/ansible-runner-service/.
 cp -r samples/project/* /usr/share/ansible-runner-service/project
```

## Building (as root, or use sudo)
1. from the ansible-runner-service directory
```
cd misc/docker
```
2. Build the container
```
docker build -f Dockerfile -t runner-service .
```

## Running the container
### basic - no persistence (i.e. not much use, just a quick test)
```
docker run -d --network=host -p 5001:5001/tcp --name runner-service runner-service
```

### with persistence
Here's an example of using the container that perists state to the host's filesystem.
```
docker run -d --network=host -p 5001:5001/tcp -v /usr/share/ansible-runner-service:/usr/share/ansible-runner-service -v /etc/ansible-runner-service:/etc/ansible-runner-service --name runner-service runner-service
```

Be aware that the container will need access to these bind-mounted locations, so you may need to ensure file and selinux permissions are set correctly.


At this point, the container persists the following content;
- ssh keys
- inventory
- playbooks
- artifacts (job/playbook run output)
