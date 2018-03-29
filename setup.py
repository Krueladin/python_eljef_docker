# -*- coding: UTF-8 -*-
"""Setup script"""

import sys
from setuptools import setup
from eljef.docker.__version__ import VERSION as EJD_VERSION

if sys.version_info[0] < 3:
    raise Exception('ElJef tools only support python version 3.6 or higher.')
if sys.version_info[0] > 3 and sys.version_info[1] < 6:
    raise Exception('ElJef tools only support python version 3.6 or higher.')

setup(
    author='Jef Oliver',
    author_email='jef@eljef.me',
    description='Functions for working with Docker containers.',
    entry_points={
        'console_scripts': [
            'eljef-docker = eljef.docker.cli.__main__:main'
        ]
    },
    install_requires=['eljef_core>=0.0.11', 'docker>=3.1'],
    license='LGPLv2.1',
    name='eljef_docker',
    packages=['eljef.docker', 'eljef.docker.cli'],
    python_requires='>=3.6',
    url='https://github.com/eljef/python_eljef_docker',
    version=EJD_VERSION,
    zip_safe=False,
)
