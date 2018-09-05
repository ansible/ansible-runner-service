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
           pexpect python-daemon  bubblewrap \
           bzip2  openssh openssh-clients python2-psutil\
           python34 python34-setuptools python34-psutil python34-crypto \
           python34-pip python34-docutils python34-paramiko && \
    localedef -c -i en_US -f UTF-8 en_US.UTF-8 && \
    pip3 install PyYAML pyOpenSSL flask flask-restful && \
    pip3 install --no-cache-dir ansible-runner && \
    rm -rf /var/cache/yum

RUN mkdir -p /etc/ansible-runner-service && \
    mkdir -p /root/.ssh && \
    mkdir -p /usr/share/ansible-runner-service

COPY ./ansible-runner-service.tar.gz /root/.
WORKDIR /root
RUN tar xvzf ansible-runner-service.tar.gz && \
    cd ansible-runner-service && \
    python3 setup.py install --record installed_files \
           --single-version-externally-managed

ENTRYPOINT ["/usr/bin/ansible-runner-service"]
