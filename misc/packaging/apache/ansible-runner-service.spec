%global srcname ansible-runner-service

Name: %{srcname}
Version: 1.0.7
Release: 1%{?dist}
Summary: RESTful API for ansible/ansible_runner execution
Source0: https://github.com/ansible/%{name}/archive/%{name}-%{version}.tar.gz
Patch0:  ovirt_log.patch
Patch1:  wsgi.patch
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
Requires: policycoreutils-python-utils
Requires: python3
Requires: python3-ansible-runner
Requires: python3-pyOpenSSL
Requires: python3-netaddr
Requires: python3-notario
Requires: python3-flask
Requires: python3-flask-restful
Requires: python3-psutil

%global _description %{expand:
This package provides the Ansible Runner Service source files. Ansible runner service exposes a REST API interface on top of the functionality provided by ansible and ansible_runner.

The Ansible Runner Service provided in this packages is intended to be used as uwgsi app exposed by Nginx in a Container.
Dependencies, and configuration tasks must be performed in the container.

Ansible Runner Service listens on https://localhost:5001 by default for playbook or ansible inventory requests. For developers interested in using the API, all the available endpoints are documented at https://localhost:5001/api.

In addition to the API endpoints, the daemon also provides a /metrics endpoint for prometheus integration. A sample Grafana dashboard is provided within /usr/share/doc/ansible-runner-service}

%description %_description

%prep
%setup -q -n %{name}-%{version}
%patch0 -p1
%patch1 -p1

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

mkdir -p %{buildroot}%{_var}/www/runnner
install -m 644 ./wsgi.py %{buildroot}%{_var}/www/runnner/runner.wsgi

%post
semanage fcontext -a -t httpd_log_t -s system_u /var/log/ovirt-engine/ansible-runner-service.log 2> /dev/null || semanage fcontext -m -t httpd_log_t -s system_u /var/log/ovirt-engine/ansible-runner-service.log || true
[[ -f /var/log/ovirt-engine/ansible-runner-service.log ]] && restorecon -rF /var/log/ovirt-engine/ansible-runner-service.log || true

%files -n %{srcname}
%{_bindir}/ansible_runner_service
%{python3_sitelib}/*
%{_sysconfdir}/logrotate.d/ansible-runner-service
%config(noreplace) %{_sysconfdir}/ansible-runner-service/*
%{_var}/www/runnner/runner.wsgi

%license LICENSE.md

%doc README.md

%changelog
* Tue Feb 2 2021 Martin Perina <mperina@redhat.com> 1.0.7-1
- Fix oVirt logging
- UBI8 Image Rebase
- Fix post script error in Apache
- Add proper logging when decoding JSON has failed
- Add ignore for partial.json.tmp
- Remove finished task from cache instead of the last one

* Thu Oct 13 2020 Martin Necas <mnecas@redhat.com> 1.0.6-3
- Fix post script error

* Thu Oct 01 2020 Martin Necas <mnecas@redhat.com> 1.0.6-2
- Fix wsgi patch

* Wed Sep 23 2020 Martin Perina <mnecas@redhat.com> 1.0.6-1
- Use permanent selinux label on logs
- Add periodic artifacts removal to wsgi based invocations

* Tue Jul 28 2020 Martin Necas <mnecas@redhat.com> 1.0.5-1
- Change artifacts_remove_age for weekly cleanup
- Fix ansible-runner-service.log permissions

* Mon Jul 13 2020 Martin Necas <mnecas@redhat.com> 1.0.4-1
- Fixes log rotation for Apache and Gunicorn based instances
- Adds mocking of SSHClient in hostvars and inventory tests

* Thu Jun 4 2020 Martin Necas <mnecas@redhat.com> 1.0.3-1
- Add logrotate configuration to purge old log files
- Add psutil to dependencies

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
