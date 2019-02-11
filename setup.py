#!/usr/bin/python

from setuptools import setup

import distutils.command.install_scripts
import shutil
import re

module_file = open("runner_service/__init__.py").read()
metadata = dict(re.findall(r"__([a-z]+)__\s*=\s*'([^']+)'", module_file))


# idea from http://stackoverflow.com/a/11400431/2139420
class StripExtension(distutils.command.install_scripts.install_scripts):
    """
    Class to handle the stripping of .py extensions in for executable file
    names making them more user friendly
    """
    def run(self):
        distutils.command.install_scripts.install_scripts.run(self)
        for script in self.get_outputs():
            if script.endswith(".py"):
                shutil.move(script, script[:-3])


setup(
    name="ansible-runner-service",
    version=metadata['version'],
    description="Ansible runner based REST API",
    long_description="Ansible runner based light weight RESTful web service",
    author="Paul Cuzner",
    author_email="pcuzner@redhat.com",
    url="http://github.com/pcuzner/ansible-runner-service",
    license="Apache2",
    packages=[
        "runner_service",
        "runner_service/controllers",
        "runner_service/services"
    ],
    scripts=[
        'ansible_runner_service.py'
    ],
    include_package_data=True,
    zip_safe=False,
    data_files=[],
    cmdclass={
        "install_scripts": StripExtension
    }
)
