# -*- coding: UTF-8 -*-
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
# image.py : Docker Images
"""ElJef Docker Image operations.

This module holds functionality for performing operations on Docker images.
"""
import logging
import json
import docker

from docker.errors import ImageNotFound

from eljef.core.check import version_check

LOGGER = logging.getLogger(__name__)

version_check(3, 6)


class DockerImage(object):
    """Docker Image interaction class

    Args:
        client: Initialized DockerClient class (Required)
        image_name: Image name

    Keyword Args:
        build_path (str): Path to directory containing Dockerfile.
                          For images to be built locally.
        build_squash (bool): Squash the build image. (Remove intermediate layers.)
        insecure_registry (bool): Registry that image is in is insecure
        username (str): Username for connecting to registry. If the username is defined, `password` is required.
        password (str): Password for connecting to registry
    """
    def __init__(self, client: docker.DockerClient, image_name: str, **kwargs) -> None:
        self.__args = self.__args_dict(kwargs.get('insecure_registry', False),
                                       kwargs.get('username', None),
                                       kwargs.get('password', None))
        self.__build_args = {'path': kwargs.get('build_path', None),
                             'pull': True,
                             'rm': kwargs.get('build_squash', True),
                             'squash': kwargs.get('build_squash', True)}
        self.__client = client
        self.__image = image_name
        self.__tag = 'latest'
        if ':' in image_name:
            self.__image, self.__tag = image_name.rsplit(':', 1)

    @staticmethod
    def __args_dict(insecure_registry, username, password) -> dict:
        kw_args = {'stream': True}

        if insecure_registry:
            kw_args['insecure_registry'] = insecure_registry
        if username or password:
            kw_args['auth_config'] = {
                'username': username,
                'password': password
            }

        return kw_args

    @staticmethod
    def __log_build_pull(line: str) -> None:
        r_data = json.loads(line)
        log_line = ''
        if 'id' in r_data:
            log_line += "ID: {0!s} | ".format(r_data['id'])
        if 'status' in r_data:
            log_line += "{0!s}".format(r_data['status'])
        elif 'stream' in r_data:
            log_line += "{0!s}".format(r_data['stream'].strip())
        LOGGER.debug(log_line)

    def _build(self) -> None:
        """Build a local image."""
        LOGGER.debug("Building image - %s:%s:%s", self.__build_args['path'], self.__image, self.__tag)

        build = self.__client.api.build
        for line in build(**self.__build_args, tag=self.__tag):
            self.__log_build_pull(line)

    def _pull(self) -> None:
        """Pull an image from a registry."""
        LOGGER.debug("Pulling image - %s:%s", self.__image, self.__tag)

        pull = self.__client.api.pull
        for line in pull(self.__image, tag=self.__tag, **self.__args):
            self.__log_build_pull(line)

    def exists(self) -> bool:
        """Determines if the containers image exists on the system.

        Returns:
            True if containers image exists, False otherwise.
        """
        LOGGER.debug("Searching for image '%s'", self.__image)
        try:
            t_image = self.__client.images.get(self.__image)
            LOGGER.debug("Found image for '%s' with ID '%s'", self.__image, t_image.short_id)
            return True
        except ImageNotFound as err:
            LOGGER.debug(err.explanation)
            return False

    def pull(self) -> None:
        """Pull or Build an Image."""
        if not self.__build_args['path']:
            self._pull()
        else:
            self._build()
