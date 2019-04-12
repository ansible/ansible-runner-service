FROM centos:7

# python2 CentOS packages
# python2-flask-restful python-flask python-crypto pyOpenSSL
# python2-psutil python-pip
# python-daemon (pulled in by pip3 install of ansible-runner)
# python-wheel
# PyYAML


# Install Ansible Runner
RUN yum -y install epel-release  && \
    yum -y install bash wget unzip ansible \
           pexpect python-daemon  bubblewrap gcc \
           bzip2  openssh openssh-clients python2-psutil\
           python36 python36-devel python36-setuptools && \
           localedef -c -i en_US -f UTF-8 en_US.UTF-8
RUN easy_install-3.6 -d /usr/lib/python3.6/site-packages pip && \
    ln -s /usr/lib/python3.6/site-packages/pip3 /usr/local/bin/pip3
RUN /usr/local/bin/pip3 install crypto docutils psutil paramiko PyYAML \
                 pyOpenSSL flask flask-restful && \
    /usr/local/bin/pip3 install --no-cache-dir ansible-runner==1.3.2 && \
    rm -rf /var/cache/yum

RUN mkdir -p /etc/ansible-runner-service && \
    mkdir -p /root/.ssh && \
    mkdir -p /usr/share/ansible-runner-service/{artifacts,env,project,inventory}

COPY ./ansible-runner-service.tar.gz /root/.
WORKDIR /root
RUN tar xvzf ansible-runner-service.tar.gz && \
    cd ansible-runner-service && \
    python36 setup.py install --record installed_files \
           --single-version-externally-managed

ENTRYPOINT ["/usr/local/bin/ansible_runner_service"]
