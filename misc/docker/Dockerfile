FROM centos:7

# Install Ansible Runner
RUN yum -y install epel-release  && \
    yum -y install bash wget unzip ansible python-psutil python-wheel \
           pexpect python-daemon python2-psutil python-pip bubblewrap \
           bzip2 python-crypto openssh openssh-clients \
           python2-flask-restful PyYAML python-flask && \
    localedef -c -i en_US -f UTF-8 en_US.UTF-8 && \
    pip install --no-cache-dir ansible-runner && \
    rm -rf /var/cache/yum

RUN mkdir -p /etc/ansible-runner-service && \
    mkdir -p /root/.ssh && \
    mkdir -p /usr/share/ansible-runner-service

COPY ./ansible-runner-service.tar.gz /root/.
WORKDIR /root
RUN tar xvzf ansible-runner-service.tar.gz && \
    cd ansible-runner-service && \
    python setup.py install --record installed_files \
           --single-version-externally-managed

ENTRYPOINT ["/usr/bin/ansible-runner-service"]
