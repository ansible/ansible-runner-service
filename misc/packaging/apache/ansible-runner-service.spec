%global srcname ansible-runner-service

Name: %{srcname}
Version: 1.0.1
Release: 1%{?dist}
Summary: RESTful API for ansible/ansible_runner execution
Source0: https://github.com/ansible/%{name}/archive/%{name}-%{version}.tar.gz
Group:	 Applications/System
License: ASL 2.0

BuildArch: noarch

BuildRequires: systemd

Requires: ansible
Requires: ansible-runner
Requires: bubblewrap
Requires: openssl
Requires: openssh
Requires: openssh-clients

%global _description %{expand:
This package provides the Ansible Runner Service source files. Ansible runner service exposes a REST API interface on top of the functionality provided by ansible and ansible_runner.

The Ansible Runner Service provided in this packages is intended to be used as uwgsi app exposed by Nginx in a Container.
Dependencies, and configuration tasks must be performed in the container.

Ansible Runner Service listens on https://localhost:5001 by default for playbook or ansible inventory requests. For developers interested in using the API, all the available endpoints are documented at https://localhost:5001/api.

In addition to the API endpoints, the daemon also provides a /metrics endpoint for prometheus integration. A sample Grafana dashboard is provided within /usr/share/doc/ansible-runner-service}

%description %_description

%package -n python2-%{srcname}
Summary:        %{summary}
BuildRequires: python2-devel
BuildRequires: python2-setuptools
Requires: python2
Requires: python2-netaddr
Requires: python2-pyOpenSSL
Requires: python2-netaddr
Requires: python2-notario
Requires: python2-flask
Requires: python2-flask-restful

%description -n python2-%{srcname} %_description

%package -n python3-%{srcname}
Summary:        %{summary}
BuildRequires: python3-devel
BuildRequires: python3-setuptools
Requires: python3
Requires: python3-netaddr
Requires: python3-pyOpenSSL
Requires: python3-netaddr
Requires: python3-notario
Requires: python3-flask
Requires: python3-flask-restful

%description -n python3-%{srcname} %_description

%prep
%setup -q -n %{name}-%{version}

%build
# Disable debuginfo packages
%define _enable_debug_package 0
%define debug_package %{nil}

%{__python2} setup.py build
%{__python3} setup.py build

%install

%{__python2} setup.py install -O1 --skip-build --root %{buildroot}
%{__python3} setup.py install -O1 --skip-build --root %{buildroot}

mkdir -p %{buildroot}%{_sysconfdir}/ansible-runner-service
install -m 644 ./config.yaml %{buildroot}%{_sysconfdir}/ansible-runner-service
install -m 644 ./logging.yaml %{buildroot}%{_sysconfdir}/ansible-runner-service

%files -n python2-%{srcname}
%{_bindir}/ansible_runner_service
%{python2_sitelib}/*
%{_sysconfdir}/ansible-runner-service/*

%license LICENSE.md

%doc README.md

%files -n python3-%{srcname}
%{_bindir}/ansible_runner_service
%{python3_sitelib}/*
%{_sysconfdir}/ansible-runner-service/*

%license LICENSE.md

%doc README.md

%changelog
* Mon Sep 2 2019 Ondra Machacek <omachace@redhat.com> 1.0.0-1
- Release 1.0.0-1.
