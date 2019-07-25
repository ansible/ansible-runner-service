# Running ansible-runner-service production container

## Goal:
Provide a container version of the ansible runner service running in 'prod' mode.
This version uses Nginx and uwsgi to provide a production environment for the
Ansible Runner Service Flask application.
While lightweight and easy to use, Flask’s built-in server is not suitable for
production as it doesn’t scale well, and also for performance and security issues.

Besides, a mechanism for provide mutual TLS authentication has been configured in the nginx server.
This allows limits the use of the system to only those computers where the right client certificates are installed

The container runs ansible runner service with bind mounts out to the local filesystem
to provide runtime, playbooks and artifacts persistence, and access to SSl certificates.
This approach allows you to install an rpm containing the playbooks specific to ceph or gluster, then map these
through to the Container.

The provided container uses CentOS with Python 3.6 (most of the development work is being done against Fedora, with Python3.6).

## Local Preparation
1. download the project to your home directory and untar/unzip

2. set up you local environment to persist the config
```
 sudo mkdir /etc/ansible-runner-service
 sudo mkdir -p /usr/share/ansible-runner-service/{artifacts,env,inventory,project}
 sudo mkdir -p /etc/ansible-runner-service/certs/{client,server}
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

5. Install certificates

The TLS mutual authentication mechanism is provided by the Nginx server used to deploy the Ansible Runner Service in production environments.
In order to make it work in the most simple way, it will be needed:

- A server certificate and a client certificate signed both by the same Certificate Authority.

It is possible to generate test certificates in order to setup the system and make tests, but it is encouraged to use real certificates signed by a real certificate authority in production environments.

* The server certificate and key must be installed in */etc/ansible-runner-service/certs/server*
* The client certificates and keys could be stored in */etc/ansible-runner-service/certs/client* (is optional to store the authorized client certificates, is in the client computer where they must be stored)

If no real certificates available, a test set of certificates can be generated executing the scripts provided:

Note:
User can easily customize the certificates to satisfy his own preferences, changing the contents of the file "certificates_data.custom".
By default, the scripts generate wildcard TLS certificates (valid to be used in any computer), but it is also possible to specify a custom "CN" field for use the certificates only in the desired computers.

e.g:
```
# ./generate_certs.sh -h
generate_certs.sh [-h] [-s string] [-c string] -- Generate self signed certificates for server and client

where:
    -h  show this help text
    -s  <string> use <string> as CN parameter for the server certificate
    -c  <string> use <string> as CN parameter for the client certificate

 # ./generate_certs.sh
 ...
 Generate CA certificate, server and client wildcard certificates in /etc/ansible-runner-service/certs
 ...

 # ./generate_certs.sh -s myserver.com -c myclient.com
 ...
 Generate CA certificate, a server certificate for the server with hostname "myserver.com" and a client certificate for the computer with hostname "myclient.com"
 ...

# ./generate_client_cert.sh -h
generate_client_cert.sh [-h] [-c string] -- Generate self signed certificates for client

where:
    -h  show this help text
    -c  <string> use <string> as CN parameter for the client certificate


 ./generate_client_cert.sh -c client2.com
 ...
 Generate a client certificate ( Signed by the CA with certificate generated using generate_certs.sh) for the computer with hostname "client2.com"
 ...

```

- Configure Nginx to use these certificates in TLS connections

The provided container provides a configuration example in the following files:
```
nginx.conf: basic Nginx config file
ars_site_nginx.conf: Basic configuration for provide mutual TLS authentication in the service
```

- Use the client certificate in all the computers that need to access the Ansible Runner Service, or generate and distribute individual client certificates (if needed, the client certificates can be generated using the 'generate_client_cert.sh' script)

The client certificates must be provided to the client computers where the requests to the Ansible Runner Service are going to be executed. This means that the final user is responsible to copy the files in */etc/ansible-runner-service/certs/client* to the client computers. or generate and distribute the clien certificates.

Double check that the rights for this files allow their utilization in the client computers!


## Building (as root, or use sudo)
1. From the ansible-runner-service directory build the container
```
docker build -f Dockerfile -t runner-service .
```

NOTE
There are two Docker files available:

- Dockerfile: Use as base a "CentOS7" container image and runs the service using Python 3.6
- Dockerfile.python27: Use as base "Ansible runner 1.3.2" container image and runs the service using Python 2.7


## Running the container with persistence (only way to use the service with TLS mutual authentication)
Here's an example of using the container that persists state to the host's filesystem.
```
docker run --rm=true -d --network=host -p 5001:5001/tcp -v /usr/share/ansible-runner-service:/usr/share/ansible-runner-service -v /etc/ansible-runner-service:/etc/ansible-runner-service --name runner-service runner-service
```
**Note: Use the following command to use the Docker Hub image**
```
docker run --rm=true -d --network=host -p 5001:5001/tcp -v /usr/share/ansible-runner-service:/usr/share/ansible-runner-service -v /etc/ansible-runner-service:/etc/ansible-runner-service --name runner-service jolmomar/ansible_runner_service
```

Be aware because the container will need access to these bind-mounted locations, so you may need to ensure file and selinux permissions are set correctly.

```
cd /usr/share
chcon -Rt container_file_t ansible-runner-service

```

At this point, the container persists the following content;
- ssh keys
- inventory
- playbooks
- artifacts (job/playbook run output)

## Using Ansible Runner Service

### curl examples

NOTE: Be sure to execute the commands in the same folder where the client certificate and key are stored. And check that the user that is going to execute the command has the rights to read these files. In all the examples, the curl command is executed in the same folder where the certificate files are stored.

Remember that the API endpoint (https://localhost:5001/api) presents <'curl'> command examples for every API endpoint.

1. Get the list of available playbooks

```
$ curl -i -k --key ./client.key --cert ./client.crt https://localhost:5001/api/v1/playbooks -X GET
HTTP/1.0 200 OK
Content-Type: application/json
Content-Length: 179
Server: Werkzeug/0.12.2 Python/3.6.6
Date: Sun, 09 Sep 2018 22:51:21 GMT

{
    "status": "OK",
    "msg": "",
    "data": {
        "playbooks": [
            "osd-configure.yml",
            "test.yml",
            "probe-disks.yml"
        ]
    }
}
```

2. Check that is not possible to use the API without using the client certificate
```
$ curl -k -i  https://localhost:5001/api/v1/groups
HTTP/1.1 400 Bad Request
Server: nginx/1.12.2
Date: Wed, 20 Mar 2019 10:02:48 GMT
Content-Type: text/html
Content-Length: 253
Connection: close

<html>
<head><title>400 No required SSL certificate was sent</title></head>
<body bgcolor="white">
<center><h1>400 Bad Request</h1></center>
<center>No required SSL certificate was sent</center>
<hr><center>nginx/1.12.2</center>
</body>
</html>
```

### Using Chrome to access Ansible Runner Service

It will be needed to add the client certificate to the system NSS Shared DB.

See: https://chromium.googlesource.com/chromium/src/+/HEAD/docs/linux_cert_management.md

Example (with one of the self-generated client self-signed certificate):


1. Export the certificate to pfx/PKCS #12 file
```
$ openssl pkcs12 -export -out client.pfx -inkey client.key -in client.crt
Enter Export Password:
Verifying - Enter Export Password:
```

2. Import the certificate to the system NSS Shared DB:
```
$ sudo pk12util -d sql:$HOME/.pki/nssdb -i client.pfx
Enter password for PKCS12 file:
pk12util: no nickname for cert in PKCS12 file.
pk12util: using nickname: AnsibleRunnerService - Red Hat
pk12util: PKCS12 IMPORT SUCCESSFUL
```
NOTE: ONCE GENERATED, BE SURE THAT THE "client.pfx" FILE CAN BE READED BY THE
      THE USERS  (SPECIFICALLY BY THE USER THAT RUNS CHROME)

3. Check that the certificate is imported:
```
$ certutil -d sql:$HOME/.pki/nssdb -L

Certificate Nickname                                         Trust Attributes
                                                             SSL,S/MIME,JAR/XPI

* - Red Hat                               u,u,u
```

4. Now the Ansible Runner Service is accesible using Chrome:

Check that you can see the API page typing the following url in chrome:
https://localhost:5001/api

Is not needed to restart Chrome, if everything is ok, Chrome will ask the first
time for the certificate to use.


NOTE:
If it is needed, the imported client certificate can be deleted using:
```
$ sudo certutil -d sql:$HOME/.pki/nssdb -D -n "AnsibleRunnerService - Red Hat"
```


## Example: Installing Ansible Runner Service in a clean CentOS 7 server


### Install docker in the host

```
# sudo yum install docker
# sudo systemctl enable docker.service
# sudo systemctl start docker.service
```
### Create in the host the needed folders

```
# sudo mkdir /etc/ansible-runner-service
# sudo mkdir -p /usr/share/ansible-runner-service/{artifacts,env,inventory,project}

# sudo chmod ug+wrx /usr/share/ansible-runner-service{artifacts,env,inventory,project}
# sudo chmod ug+wrx /etc/ansible-runner-service
```

### To allow copy/modify files from inside the container

```
# cd /usr/share
# sudo chcon -Rt container_file_t ansible-runner-service
# cd /etc
# sudo chcon -Rt container_file_t ansible-runner-service
```

### Instead of copy information from another external source , use the files in the container to configure the environment:

In the CentOS 7 server:
```
# sudo docker run --rm=true -d --network host -v /usr/share/ansible-runner-service:/usr/share/ansible-runner-service -v /etc/ansible-runner-service:/etc/ansible-runner-service --name runner-service jolmomar/ansible_runner_service:latest
# sudo docker ps -a
# sudo docker logs runner-service  <----- It can't start ... needed to copy first config files, playbooks to execute and generate certs
# sudo docker exec -it  runner-service bash
```

In the container:
```
# cd ansible-runner-service
# cp {logging,config}.yaml /etc/ansible-runner-service/.
# cp -r samples/project/* /usr/share/ansible-runner-service/project
# cd misc/nginx/
# ./generate_certs.sh
# exit
```

### Restart the container to apply the new configuration

In the CentOS 7 server, we have "extracted/generated" the config files/certificates/playbooks needed. We must restart the container in order to use the new settings

```
# sudo docker rm -f runner-service
# sudo docker ps -a  <---- should appear empty
# sudo docker run --rm=true -d --network host -v /usr/share/ansible-runner-service:/usr/share/ansible-runner-service -v /etc/ansible-runner-service:/etc/ansible-runner-service --name runner-service jolmomar/ansible_runner_service:latest
# sudo docker ps -a  <--- should appear our container
# sudo docker logs runner-service  <---- just check everything ok
```

### Check that it is working:

```
# cd /etc/ansible-runner-service/certs/client/
# curl -i -k --key ./client.key --cert ./client.crt https://localhost:5001/api/v1/playbooks -X GET
```
