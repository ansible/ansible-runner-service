# Running ansible-runner-service production container

## WARNING: THIS IS A WORK IN PROGRESS!

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
2. create an archive of the project called ansible-runner-service.tar.gz and
store it in the misc/docker directory
3. set up you local environment to persist the config
```
 sudo mkdir /etc/ansible-runner-service
 sudo mkdir -p /usr/share/ansible-runner-service/{artifacts,env,inventory,project}
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

- A server certificate and a client certificate signed both for the same Certificate Authority.

It is possible to generate test certificates in order to setup the system and make tests, but it is encouraged to use real certificates signed by a real certificate authority in production environments.

* The server certificates must be installed in */etc/ansible-runner-service/certs/server*
* The client certificates must be installed in */etc/ansible-runner-service/certs/client*

If no real certificates available, a test set of certificates can be generated executing the script provided:

```
 ./generate_certs.sh

```

- Configure Nginx to use these certificates in TLS connections

The provided container provides a configuration example in the following files:
```
nginx.conf: basic Nginx config file
ars_site_nginx.conf: Basic configuration for provide mutualo TLS authentication in the service
```

- Use the client certificate in all the computers that need to access the Ansible Runner Service

The client certificates must be provided to the client computers where the requests to the Ansible Runner Service are going to be executed. This means that the final user is responsible to copy the files in */etc/ansible-runner-service/certs/client* to the client computers.

Double check that the rights for this files allow their utilization in the client computers!


## Building (as root, or use sudo)
1. from the ansible-runner-service directory
```
cd misc/nginx
```
2. Build the container
```
docker build -f Dockerfile -t runner-service .
```

## Running the container with persistence (only way to use the service with TLS mutual authentication)
Here's an example of using the container that persists state to the host's filesystem.
```
docker run -d --network=host -p 5001:5001/tcp -v /usr/share/ansible-runner-service:/usr/share/ansible-runner-service -v /etc/ansible-runner-service:/etc/ansible-runner-service --name runner-service runner-service
```

Be aware that the container will need access to these bind-mounted locations, so you may need to ensure file and selinux permissions are set correctly.

At this point, the container persists the following content;
- ssh keys
- inventory
- playbooks
- artifacts (job/playbook run output)

## Using Ansible Runner Service

### curl examples (TODO: this example will be moved to the API endpoint. token & identification are going to be removed)

> All the commands used in this example are issued from the same directory where resides the client certificate and key files.
> Remember that client certificate and key files must be copied to the client computers!.

1. Get token
```
$ curl -k -i --key client.key --cert client.crt --user admin:admin https://localhost:5001/api/v1/login
HTTP/1.1 200 OK
Server: nginx/1.12.2
Date: Wed, 20 Mar 2019 10:01:20 GMT
Content-Type: application/json
Content-Length: 170
Connection: keep-alive

{"status": "OK", "msg": "Token returned", "data": {"token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE1NTMxNjI0ODB9.14RgKAC1XFI-diYmW-64sfYONnfMW6hycWPF9EhbXsk"}}
```

2. Use token to get groups
```
$ curl -k -i -H "Authorization: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE1NTMxNjI0ODB9.14RgKAC1XFI-diYmW-64sfYONnfMW6hycWPF9EhbXsk" --key client.key --cert client.crt https://localhost:5001/api/v1/groups
HTTP/1.1 200 OK
Server: nginx/1.12.2
Date: Wed, 20 Mar 2019 10:02:32 GMT
Content-Type: application/json
Content-Length: 74
Connection: keep-alive

{"status": "OK", "msg": "", "data": {"groups": ["mgrs", "mons", "osds"]}}
```

3. Check that is not possible to use the API without using the client certificate
```
$ curl -k -i -H "Authorization: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE1NTMxNjI0ODB9.14RgKAC1XFI-diYmW-64sfYONnfMW6hycWPF9EhbXsk"  https://localhost:5001/api/v1/groups
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

3. Check that the certificate is imported:
```
$ certutil -d sql:$HOME/.pki/nssdb -L

Certificate Nickname                                         Trust Attributes
                                                             SSL,S/MIME,JAR/XPI

AnsibleRunnerService - Red Hat                               u,u,u
```

4. Now the Ansible Runner Service is accesible using Chrome:

Check that you can see the API page typing the following url in chrome:
https://localhost:5001/api

Note:
If it is needed, the imported client certificate can be deleted using:
```
$ sudo certutil -d sql:$HOME/.pki/nssdb -D -n "AnsibleRunnerService - Red Hat"
```
