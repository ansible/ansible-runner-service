# Running ansible-runner-service in a container

## WARNING: THIS IS A WORK IN PROGRESS!

## Goal:
Provide a container version of the ansible runner service running in 'prod' mode

The container runs ansible runner service with bind mounts out to the local filesystem
to provide runtime, playbooks and artifacts persistence. This approach allows you to
install an rpm containing the playbooks specific to ceph or gluster, then map these
through to the Container.

At this point the container enables you to test the API, but not run anything meaningful...but it will :)


## Local Preparation
1. download the project to your home directory and untar/unzip
2. create an archive of the project called ansible-runner-service.tar.gz and
store it in the misc/docker directory
3. set up you local environment to persist the config
```
 sudo mkdir /etc/ansible-runner-service
 sudo mkdir /usr/share/ansible-runner-service
```
4. from the root of the ansible-runner-service directory
```
 cp {logging,config}.yaml /etc/ansible-runner-service/.
 cp samples/* /usr/share/ansible-runner-service/
```
*(the paths don't matter, they're just the ones I'm using for test)*

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
### basic - no persistence (i.e. not much use)
```
docker run -d --network=host -p 5001:5001/tcp --name runner-service runner-service
```

### with persistence
```
docker run -d --network=host -p 5001:5001/tcp -v /usr/share/ansible-runner-service:/usr/share/ansible-runner-service -v /etc/ansible-runner-service:/etc/ansible-runner-service --name runner-service runner-service
```

## future stuff
To make the container really useful we need to persist more 'stuff'  
```/etc/ansible/hosts``` ... to persist hosts and groups  
```/root/.ssh``` ... to perists ssh key access for passwordless ssh  

However the inclusion of the hosts and ssh keys needs additional code to support host management.
