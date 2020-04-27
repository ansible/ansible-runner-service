import runner_service.configuration as configuration
from runner_service.app import create_app
from ansible_runner_service import setup_common_environment


"""
WSGI config for Ansible Runner Service

It exposes the WSGI callable as a module-level variable named ``application``.

"""

# wsgi entry point is only for production servers
configuration.init(mode='prod')

# Setup log and ssh and other things present in all the environments
setup_common_environment()

# The object to be managed by uwsgi
application = create_app()
