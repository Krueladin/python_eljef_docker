# -*- coding: UTF-8 -*-
# pylint: disable=too-few-public-methods
# Copyright (c) 2017-2018, Jef Oliver
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU Lesser General Public License,
# version 2.1, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for
# more details.
#
# Authors:
# Jef Oliver <jef@eljef.me>
#
# docker.py : Docker operations
"""ElJef Docker operations.

This module holds functionality for performing operations on Docker containers.

TODO:
    TLS support
"""
import logging
import os
import docker

from eljef.core import fops
from eljef.core.check import version_check

from eljef.docker.containers import DockerContainers
from eljef.docker.group import DockerGroups

LOGGER = logging.getLogger(__name__)

version_check(3, 6)


class Docker(object):
    """Docker information and control class.

    Args:
        config_path: Path to base configuration directory.
        host: If the host running dockerd is remote, the hostname must should be provided in [hostname/ip]:port format.
    """
    def __init__(self, config_path: str, host: str = None) -> None:
        fops.mkdir(os.path.abspath(config_path))
        self.__client = self.__connect(host)
        self.groups = DockerGroups(config_path)
        self.containers = DockerContainers(self.__client, config_path, self.groups)

    @staticmethod
    def __connect(host: str = None) -> docker.DockerClient:
        LOGGER.debug('Creating docker connection client.')
        return docker.from_env() if host else docker.DockerClient(base_url=host)
