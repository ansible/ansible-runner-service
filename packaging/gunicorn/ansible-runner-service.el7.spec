%global srcname ansible-runner-service-dev

Name: %{srcname}
Version: 1.0.2
Release: 1%{?dist}
Summary: RESTful API for ansible/ansible_runner execution
Source0: https://github.com/ansible/%{name}/archive/%{name}-%{version}.tar.gz
Patch0:  wsgi.patch
Patch1:  ovirt_logging_path.patch
Group:	 Applications/System
License: ASL 2.0

BuildArch: noarch

BuildRequires: systemd
BuildRequires: python2-devel
BuildRequires: python2-setuptools

Requires: ansible
Requires: openssl
Requires: openssh
Requires: openssh-clients
Requires: python-gunicorn
Requires: python2
Requires: python2-ansible-runner
Requires: python2-pyOpenSSL
Requires: python2-netaddr
Requires: python2-notario
Requires: python2-flask
Requires: python2-flask-restful
Requires: python2-psutil

%global _description %{expand:
This package provides the Ansible Runner Service source files. Ansible runner service exposes a REST API interface on top of the functionality provided by ansible and ansible_runner.

The Ansible Runner Service provided in this packages is intended to be used as uwgsi app exposed by Nginx in a Container.
Dependencies, and configuration tasks must be performed in the container.

Ansible Runner Service listens on https://localhost:50001 by default for playbook or ansible inventory requests. For developers interested in using the API, all the available endpoints are documented at https://localhost:50001/api.

In addition to the API endpoints, the daemon also provides a /metrics endpoint for prometheus integration. A sample Grafana dashboard is provided within /usr/share/doc/ansible-runner-service}

%description %_description

%prep
%setup -q -n ansible-runner-service-%{version}
%patch0 -p1
%patch1 -p1

%build
# Disable debuginfo packages
%define _enable_debug_package 0
%define debug_package %{nil}

%{__python2} setup.py build

%install

%{__python2} setup.py install -O1 --skip-build --root %{buildroot}

mkdir -p %{buildroot}%{_sysconfdir}/ansible-runner-service
install -m 644 ./config.yaml %{buildroot}%{_sysconfdir}/ansible-runner-service
install -m 644 ./logging.yaml %{buildroot}%{_sysconfdir}/ansible-runner-service

install -m 644 ./wsgi.py %{buildroot}%{python2_sitelib}/runner_service/
install -m 644 ./ansible_runner_service.py %{buildroot}%{python2_sitelib}/runner_service

mkdir -p %{buildroot}%{_unitdir}
cp -r ./packaging/gunicorn/ansible-runner-service.service %{buildroot}%{_unitdir}

mkdir -p %{buildroot}/var/log/ovirt-engine
touch %{buildroot}/var/log/ovirt-engine/ansible-runner-service.log

mkdir -p %{buildroot}%{_sysconfdir}/logrotate.d
install -m 644 ./packaging/gunicorn/ansible-runner-service %{buildroot}%{_sysconfdir}/logrotate.d/ansible-runner-service

%files -n %{srcname}
%{_bindir}/ansible_runner_service
%{python2_sitelib}/*
%config(noreplace) %{_sysconfdir}/ansible-runner-service/config.yaml
%config %{_sysconfdir}/ansible-runner-service/logging.yaml
%{_unitdir}/ansible-runner-service.service
%{_sysconfdir}/logrotate.d/ansible-runner-service
/var/log/ovirt-engine/ansible-runner-service.log

%license LICENSE.md

%doc README.md

%changelog
* Tue Apr 28 2020 Martin Necas <mnecas@redhat.com> 1.0.2-1
- Allow playbook parallel execution.
- Add artifacts removal.
- Apply logging configurations.
- Handle connection to IPv6 hosts.

* Tue Oct 22 2019 Ondra Machacek <omachace@redhat.com> 1.0.1-1
- Set runner_cache as defaultdict of dict.
- Define ConnectionRefusedError for Python2.
- Add ssh_private_key configuration option.
- Add support to specify host port.
- Add spec files.

* Mon Sep 2 2019 Ondra Machacek <omachace@redhat.com> 1.0.0-1
- Release 1.0.0-1.
