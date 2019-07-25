FROM centos:7

# Install dependencies
RUN yum -y install epel-release  && \
    yum -y install bash wget unzip \
           pexpect python-daemon  bubblewrap gcc \
           bzip2  openssh openssh-clients python2-psutil\
           python36 python36-devel python36-setuptools\
           nginx supervisor && \
           localedef -c -i en_US -f UTF-8 en_US.UTF-8
RUN easy_install-3.6 -d /usr/lib/python3.6/site-packages pip && \
    ln -s /usr/lib/python3.6/site-packages/pip3 /usr/local/bin/pip3

RUN /usr/local/bin/pip3 install ansible cryptography docutils psutil PyYAML \
                 pyOpenSSL flask flask-restful uwsgi netaddr notario && \
    /usr/local/bin/pip3 install --no-cache-dir ansible-runner==1.3.2 && \
    rm -rf /var/cache/yum

# Prepare folders for shared access and ssh
RUN mkdir -p /etc/ansible-runner-service && \
    mkdir -p /root/.ssh && \
    mkdir -p /usr/share/ansible-runner-service/{artifacts,env,project,inventory,client_cert}

# Install Ansible Runner
WORKDIR /root
COPY ./*.py ansible-runner-service/
COPY ./*.yaml ansible-runner-service/
COPY ./runner_service ansible-runner-service/runner_service
COPY ./samples ansible-runner-service/samples

# Put configuration files in the right places
# Nginx configuration
COPY misc/nginx/nginx.conf /etc/nginx/
# Ansible Runner Service nginx virtual server
COPY misc/nginx/ars_site_nginx.conf /etc/nginx/conf.d
# Ansible Runner Service uwsgi settings
COPY misc/nginx/uwsgi.ini /root/ansible-runner-service
# Supervisor start sequence
COPY misc/nginx/supervisord.conf /root/ansible-runner-service

# Start services
CMD ["/usr/bin/supervisord", "-c", "/root/ansible-runner-service/supervisord.conf"]
