%global srcname ansible-runner-service

Name: %{srcname}
Version: 1.0.2
Release: 1%{?dist}
Summary: RESTful API for ansible/ansible_runner execution
Source0: https://github.com/ansible/%{name}/archive/%{name}-%{version}.tar.gz
Group:	 Applications/System
License: ASL 2.0

BuildArch: noarch

BuildRequires: systemd
BuildRequires: python3-devel
BuildRequires: python3-setuptools

Requires: ansible
Requires: logrotate
Requires: openssl
Requires: openssh
Requires: openssh-clients
Requires: python3
Requires: python3-ansible-runner
Requires: python3-pyOpenSSL
Requires: python3-netaddr
Requires: python3-notario
Requires: python3-flask
Requires: python3-flask-restful

%global _description %{expand:
This package provides the Ansible Runner Service source files. Ansible runner service exposes a REST API interface on top of the functionality provided by ansible and ansible_runner.

The Ansible Runner Service provided in this packages is intended to be used as uwgsi app exposed by Nginx in a Container.
Dependencies, and configuration tasks must be performed in the container.

Ansible Runner Service listens on https://localhost:5001 by default for playbook or ansible inventory requests. For developers interested in using the API, all the available endpoints are documented at https://localhost:5001/api.

In addition to the API endpoints, the daemon also provides a /metrics endpoint for prometheus integration. A sample Grafana dashboard is provided within /usr/share/doc/ansible-runner-service}

%description %_description

%prep
%setup -q -n %{name}-%{version}

%build
# Disable debuginfo packages
%define _enable_debug_package 0
%define debug_package %{nil}

%{__python3} setup.py build

%install

%{__python3} setup.py install -O1 --skip-build --root %{buildroot}

mkdir -p %{buildroot}%{_sysconfdir}/ansible-runner-service
install -m 644 ./config.yaml %{buildroot}%{_sysconfdir}/ansible-runner-service
install -m 644 ./logging.yaml %{buildroot}%{_sysconfdir}/ansible-runner-service

mkdir -p %{buildroot}%{_sysconfdir}/logrotate.d
install -m 644 ./misc/packaging/logrotate/ansible-runner-service %{buildroot}%{_sysconfdir}/logrotate.d/ansible-runner-service

install -m 644 ./ansible_runner_service.py %{buildroot}%{python3_sitelib}/runner_service

%files -n %{srcname}
%{_bindir}/ansible_runner_service
%{python3_sitelib}/*
%{_sysconfdir}/ansible-runner-service/*
%{_sysconfdir}/logrotate.d/ansible-runner-service
%config(noreplace) %{_sysconfdir}/ansible-runner-service/*

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
