%if 0%{?rhel} == 7
  # Building on CentoOS 7 would result in ".el7.centos"
  %define dist .el7
%endif

Name: ansible-runner-service
Version: 0.9
Release: 3%{?dist}
Summary: RESTful API for ansible/ansible_runner execution
Source0: https://github.com/pcuzner/%{name}/archive/%{name}-%{version}.tar.gz
Group:	 Applications/System
License: ASL 2.0

BuildArch: noarch


%description
This package provides the Ansible Runner Service source files. Ansible runner service exposes a REST API interface on top of the functionality provided by ansible and ansible_runner.

The Ansible Runner Service provided in this packages is intended to be used as uwgsi app exposed by Nginx in a Container.
Dependencies, and configuration tasks must be performed in the container.

Ansible Runner Service listens on https://localhost:5001 by default for playbook or ansible inventory requests. For developers interested in using the API, all the available endpoints are documented at https://localhost:5001/api.

In addition to the API endpoints, the daemon also provides a /metrics endpoint for prometheus integration. A sample Grafana dashboard is provided within /usr/share/doc/ansible-runner-service

%prep
%setup -q -n %{name}-%{version}

%build
# Disable debuginfo packages
%define _enable_debug_package 0
%define debug_package %{nil}

%{__python} setup.py build

%install
%{__python} setup.py install -O1 --skip-build --root %{buildroot} --install-scripts /usr/bin
mkdir -p %{buildroot}%{_unitdir}
install -m 0644 ./misc/systemd/ansible-runner-service.service %{buildroot}%{_unitdir}
mkdir -p %{buildroot}%{_sysconfdir}/ansible-runner-service
install -m 0644 ./config.yaml %{buildroot}%{_sysconfdir}/ansible-runner-service
install -m 0644 ./logging.yaml %{buildroot}%{_sysconfdir}/ansible-runner-service
mkdir -p %{buildroot}%{_prefix}/share/ansible-runner-service/artifacts
mkdir -p %{buildroot}%{_prefix}/share/ansible-runner-service/env
mkdir -p %{buildroot}%{_prefix}/share/ansible-runner-service/inventory
mkdir -p %{buildroot}%{_prefix}/share/ansible-runner-service/project
install -m 0644 ./samples/project/runnertest.yml %{buildroot}%{_prefix}/share/ansible-runner-service/project
mkdir -p %{buildroot}%{_docdir}/ansible-runner-service/dashboards
install -m 0644 ./misc/dashboards/ansible-runner-service-metrics.json  %{buildroot}%{_docdir}/ansible-runner-service/dashboards
install -m 0644 ./LICENSE.md %{buildroot}%{_docdir}/ansible-runner-service

%post


%postun


%files
%{_bindir}/ansible_runner_service
%{python_sitelib}/*
%{_prefix}/share/ansible-runner-service/*
%{_sysconfdir}/ansible-runner-service/*
%{_unitdir}/ansible-runner-service.service
%{_docdir}/ansible-runner-service/*

%changelog
* Thu Jun 20 2019 Juan Miguel Olmo <jolmomar@redhat.com> 0.9-3
- Initial rpm packaging to use Ansible Runner Service in containers
