# -*- coding: UTF-8 -*-
# Copyright (c) 2017, Jef Oliver
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
# containers.py : Docker Containers
"""ElJef Docker Containers operations.

This module holds functionality for performing operations on Docker Containers.
"""
import docker
import logging
import os

from eljef.core import fops
from eljef.core.check import version_check
from eljef.core.dictobj import DictObj

from eljef.docker.exceptions import ConfigError
from eljef.docker.exceptions import DockerError
from eljef.docker.group import DockerGroups
from eljef.docker.image import DockerImage

LOGGER = logging.getLogger(__name__)

version_check(3, 6)

VALIDATE_TE = "Incorrect key type: '{0!s}' is '{1!s}' but needs to be '{2!s}'"
VALIDATE_TE_LIST = "Incorrect list contents: Value at position '{0!s}' in "\
                   "key '{1!s} has a type of '{2!s}' when it should be 'str'"


class ContainerOpts(DictObj):
    """Docker Container options class"""
    def __init__(self):
        super().__init__()
        self.cap_add = []
        self.cap_drop = []
        self.devices = []
        self.dns = []
        self.environment = []
        self.group = ''
        self.image = ''
        self.image_args = []
        self.image_insecure = False
        self.image_password = ''
        self.image_username = ''
        self.mounts = []
        self.name = ''
        self.net = ''
        self.network = ''
        self.ports = []
        self.restart = ''


def _build_command_dict(options: ContainerOpts) -> dict:
    ret = dict()
    for attr in {'cap_add', 'cap_drop', 'devices', 'dns', 'environment'}:
        data = getattr(options, attr)
        if len(data) > 0:
            ret[attr] = data

    ret['restart_policy'] = 'always'
    if options.restart:
        ret['restart_policy'] = options.restart

    ret['name'] = options.name

    if options.network:
        ret['network'] = options.network
    elif options.net:
        ret['network_mode'] = "container:{0!s}".format(options.net)

    if len(options.mounts) > 0:
        volumes = dict()
        for vol in options.mounts:
            host_path, cont_path, mode = None, None, None
            vol_dict = dict()
            if vol.count(':') == 1:
                host_path, cont_path = vol.split(':')
            elif vol.count(':') == 2:
                host_path, cont_path, mode = vol.split(':')
            else:
                raise ConfigError("Malformed Path: {0!s}".format(vol))

            if not mode or mode not in {'ro', 'rw'}:
                mode = 'rw'

            vol_dict['bind'] = cont_path
            vol_dict['mode'] = mode
            volumes[host_path] = vol_dict
        ret['volumes'] = volumes

    if len(options.ports) > 0:
        ports = dict()
        for port_group in options.ports:
            host_port, cont_port = port_group.split(':')
            ports[cont_port] = host_port
        ret['ports'] = ports

    if len(options.image_args) > 0:
        ret['command'] = options.image_args

    return ret


def validate_container_options(options: dict) -> ContainerOpts:
    """Validate incoming option types to provide base sanity

    Args:
        options: Dictionary of options to be used with docker. (Typically fed
                 from a YAML config file.

    Returns:
        A filled ContainerOpts information holder.

    Raises:
        ConfigError: If type of data is incorrect or data is missing.
   """
    validated = ContainerOpts()
    for key, value in validated:
        if key in options:
            data = options[key]
            if type(data) in {bytes, str}:
                data = fops.makestr(data)
            if type(data) != type(value):
                k_is = type(data).__name__
                k_sb = type(value).__name__
                err_s = VALIDATE_TE.format(key, k_is, k_sb)
                raise ConfigError(err_s)
            if data == '':
                data = None
            if type(data) == list:
                c = 0
                while c < len(data):
                    if type(data[c]) not in {bytes, str}:
                        k_is = type(data[c]).__name__
                        err_s = VALIDATE_TE_LIST.format(c, key, k_is)
                        raise ConfigError(err_s)
            validated[key] = data

    if not validated.image:
        raise ConfigError("'image' not defined in container options.")
    if not validated.name:
        raise ConfigError("'name' not defined in container options.")

    return validated


class DockerContainer(object):
    """Docker Container class

    Args:
        client: Initialized DockerClient class (Required)
        info: initialized ContainerOpts class (Required)
        image: initialized DockerImage class (Required)
    """
    def __init__(self, client: docker.DockerClient, info: ContainerOpts,
                 image: DockerImage) -> None:
        self.__client = client
        self.__container = None
        self.info = info
        self.image = image

    def __get(self):
        if not self.__container:
            self.__container = self.__client.containers.get(self.info.name)

    def dump(self) -> str:
        """Dumps the configuration for this container to a file in the
           current working directory.

        Returns:
            Path to written file.
        """
        cur_path = os.path.abspath(os.path.curdir())
        yaml_file = os.path.join(cur_path, "{0!s}.yaml".format(self.info.name))
        fops.file_write_convert(yaml_file, 'YAML', self.info.to_dict())

        LOGGER.debug("Wrote current config to: {0!s}".format(yaml_file))

        return yaml_file

    def rebuild(self) -> None:
        """Stops a container, removes it, and starts a new container with
           the stored definition.
        """
        self.stop()
        self.remove()
        self.start()

    def remove(self) -> None:
        """Removes a container."""
        self.__get()
        self.__container.remove()
        self.__container = None

    def restart(self) -> None:
        self.stop()
        self.start()

    def start(self) -> None:
        """Starts a container.

        Notes:
            The container is started in daemonized (background, detached)
            mode.
        """
        LOGGER.debug("Starting container: {0!s}".format(self.info.name))
        if self.__container:
            log_s = "Container '{0!s}' exists. Must stop() first."
            raise DockerError(log_s.format(self.info.name))

        if not self.image.exists():
            self.image.pull()

        kw_args = _build_command_dict(self.info)
        kw_args['detach'] = True

        self.__container = self.__client.containers.run(self.info.image,
                                                        **kw_args)
        LOGGER.debug("Started container: {0!s}".format(self.info.name))

    def stop(self) -> None:
        """Stops a running container."""
        LOGGER.debug("Stopping container: {0!s}".format(self.info.name))
        self.__get()
        self.__container.stop()
        LOGGER.debug("Stopped container: {0!s}".format(self.info.name))

    def update(self) -> None:
        """Updates the image for a container."""
        self.image.pull()


class DockerContainers(object):
    """Docker Containers interaction class

    Args:
        client: Initialized DockerClient class (Required)
        config_path: Path to base of configuration directory
        groups: Initialized DockerGroups class (Not required)
    """
    def __init__(self, client: docker.DockerClient, config_path: str,
                 groups: DockerGroups=None) -> None:
        self.__client = client
        self.__config_path = os.path.join(os.path.abspath(config_path),
                                          'containers')
        self.__containers = self.__list_defined()
        self.__groups = groups

    def __list_defined(self) -> dict:
        LOGGER.debug('Building a list of currently defined containers.')
        containers = dict()
        c_list = os.listdir(self.__config_path)

        for container_file in c_list:
            if container_file[-5:] == '.yaml':
                fp = os.path.join(self.__config_path, container_file)
                containers[container_file[:-5]] = fp

        return containers

    def define(self, container_def: str) -> str:
        """Adds a container via a container definition file

        Args:
            container_def: Definition file to use for adding a container.

        Returns:
            Name of newly defined container
        """
        log_s = "Reading container definition {0!s}'".format(container_def)
        LOGGER.debug(log_s)
        fd = fops.file_read_convert(container_def, 'YAML')

        log_s = "Validating container definition {0!s}".format(container_def)
        LOGGER.debug(log_s)
        t = validate_container_options(fd)

        if self.__groups and t['group']:
            if t['group'] not in self.__groups.list():
                err_s = "Container definition for '{0!s}' contains " \
                        "group that is not defined. " \
                        "Add group first.".format(t['name'])
                raise ConfigError(err_s)
            g_info = self.__groups.get(t['group'])
            if t['name'] not in g_info.members:
                g_info.members.append(t['name'])
                self.__groups.save()

        fp = os.path.join(self.__config_path, "{0!s}.yaml".format(t['name']))
        self.__containers[t['name']] = fp

        LOGGER.debug("Saving configuration for '{0!s}'".format(t['name']))
        fops.file_write_convert(fp, 'YAML', t.to_dict())

        return t.name

    def get(self, container_name: str) -> DockerContainer:
        """Returns an already defined container

        Args:
            container_name: Name of the container to return info for.

        Returns:
            DockerContainer information class
        """
        if container_name not in self.__containers:
            err_s = "Container '{0!s}' not defined."
            raise DockerError(err_s.format(container_name))

        log_s = "Reading container info for {0!s}"
        LOGGER.debug(log_s.format(container_name))
        fd = fops.file_read_convert(self.__containers[container_name], 'YAML')

        log_s = "Validating container info for {0!s}"
        LOGGER.debug(log_s.format(container_name))
        container_info = validate_container_options(fd)

        log_s = "Initializing image class for {0!s}"
        LOGGER.debug(log_s.format(container_name))
        container_image = DockerImage(self.__client, container_info.image,
                                      container_info.image_insecure,
                                      container_info.image_username,
                                      container_info.image_password)

        return DockerContainer(self.__client, container_info, container_image)

    def list(self) -> list:
        """Returns a list of currently defined containers.

        Returns:
            A list of currently defined containers.
        """
        return [*self.__containers]
