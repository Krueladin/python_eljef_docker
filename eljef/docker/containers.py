# -*- coding: UTF-8 -*-
# pylint: disable=R0902
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
# containers.py : Docker Containers
"""ElJef Docker Containers operations.

This module holds functionality for performing operations on Docker Containers.
"""
import logging
import os

from typing import Any

import docker

from docker.errors import NotFound
from docker.types.services import Mount

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
VALIDATE_TE_LIST = "Incorrect list contents: Value at position '{0!s}' in key '{1!s} has a type of '{2!s}' when it " \
                   "should be 'str'"

_ERR_CONTAINER_UNDEF_GROUP = "Container definition for '{0!s}' contains group that is not defined. Add group first."


def _save_container_file(container_name: str, file_path: str, out_dict: dict) -> None:
    LOGGER.debug("Saving configuration for '%s'", container_name)
    for i in {'group', 'image_password', 'image_username', 'image_build_path', 'net', 'network', 'restart', 'tag'}:
        if out_dict[i] is None:
            out_dict[i] = ''
    fops.file_write_convert(file_path, 'YAML', out_dict)


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
        self.image_build_path = ''
        self.image_build_squash = False
        self.mounts = []
        self.name = ''
        self.net = ''
        self.network = ''
        self.ports = []
        self.restart = ''
        self.tag = ''
        self.tmpfs = []

    def set_with_type(self, key: Any, value: Any) -> None:
        """Sets an attribute after checking type.

        This will check the type of ``value`` matches the type of ``key`` before setting.
        """
        o_value = getattr(self, key)

        if not isinstance(value, type(o_value)):
            k_is = type(value).__name__
            k_sb = type(o_value).__name__
            err_s = VALIDATE_TE.format(key, k_is, k_sb)
            raise ConfigError(err_s)
        elif isinstance(value, list):
            count = 0
            while count < len(value):
                if not isinstance(value[count], (bytes, str)):
                    k_is = type(value[count]).__name__
                    err_s = VALIDATE_TE_LIST.format(count, key, k_is)
                    raise ConfigError(err_s)
                count += 1

        setattr(self, key, None if value == '' else value)


class _CommandDict(object):
    """Docker Keyword Arguments Dictionary Builder"""
    def __init__(self, options: ContainerOpts):
        self.options = options
        self.ret = dict()

    def build(self) -> dict:
        """Builds the Keyword Dictionary to Send to docker-py

        Returns:
            dict: A dictionary of keyword arguments
        """
        self.ret['name'] = self.options.name
        self.img_args()
        self.mounts()
        self.networking()
        self.optional_attrs()
        self.ports()
        self.restart()
        self.tmpfs()

        return self.ret

    def img_args(self):
        """Adds arguments to send to docker image on startup"""
        if self.options.image_args:
            self.ret['command'] = self.options.image_args

    def mounts(self):
        """Add Volumes to Mount"""
        if self.options.mounts:
            volumes = list()

            for vol in self.options.mounts:
                host_path, cont_path, mode = None, None, None
                if vol.count(':') == 1:
                    host_path, cont_path = vol.split(':')
                elif vol.count(':') == 2:
                    host_path, cont_path, mode = vol.split(':')
                else:
                    raise ConfigError("Malformed Path: {0!s}".format(vol))

                read_only = True if mode == 'ro' else False

                mount = Mount(cont_path, host_path, type='bind', read_only=read_only, propagation='slave')
                volumes.append(mount)

            self.ret['mounts'] = volumes

    def networking(self):
        """Setup Networking"""
        if self.options.network:
            self.ret['network'] = self.options.network
        elif self.options.net:
            self.ret['network_mode'] = \
                'host' if self.options.net == 'host' else "container:{0!s}".format(self.options.net)

    def optional_attrs(self):
        """Add Optional Attributes"""
        for attr in {'cap_add', 'cap_drop', 'devices', 'dns', 'environment'}:
            data = getattr(self.options, attr)
            if data:
                self.ret[attr] = data

    def ports(self):
        """Add Port Maps"""
        if self.options.ports:
            ports = dict()
            for port_group in self.options.ports:
                host_port, cont_port = port_group.split(':')
                ports[cont_port] = host_port
            self.ret['ports'] = ports

    def restart(self):
        """Set Restart Policy"""
        self.ret['restart_policy'] = {'Name': 'always'}
        if self.options.restart:
            self.ret['restart_policy']['Name'] = self.options.restart

    def tmpfs(self):
        """Adds tmpfs mounts"""
        if self.options.tmpfs:
            t_dict = {}
            for i in self.options.tmpfs:
                if ':' in i:
                    t_var = i.split(':')
                    t_dict[t_var[0]] = t_var[1]
                else:
                    t_dict[i] = ''

            self.ret['tmpfs'] = t_dict


class DockerContainer(object):
    """Docker Container class

    Args:
        client: Initialized DockerClient class (Required)
        info: Initialized ContainerOpts class (Required)
        image: Initialized DockerImage class (Required)

    Keyword Args:
        file_p: Path to container configuration file.
    """
    def __init__(self, client: docker.DockerClient, info: ContainerOpts, image: DockerImage, **kwargs) -> None:
        self.__client = client
        self.__container = None
        self.info = info
        self.image = image
        self.file_p = kwargs.get('file_p', None)

    def __get(self):
        if not self.__container:
            try:
                self.__container = self.__client.containers.get(self.info.name)
            except NotFound:
                self.__container = None

    def dump(self) -> str:
        """Dumps the configuration for this container to a file in the
           current working directory.

        Returns:
            Path to written file.
        """
        cur_path = os.path.abspath(os.path.curdir)
        yaml_file = os.path.join(cur_path, "{0!s}.yaml".format(self.info.name))
        fops.file_write_convert(yaml_file, 'YAML', self.info.to_dict())

        LOGGER.debug("Wrote current config to: %s", yaml_file)

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

    def run(self) -> None:
        """Runs a container.

        Notes:
            The container is ran in daemonized (background, detached)
            mode.
        """
        LOGGER.debug("Running container: %s", self.info.name)
        if self.__container:
            log_s = "Container '{0!s}' exists. Must stop() and remove() first."
            raise DockerError(log_s.format(self.info.name))

        if not self.image.exists():
            self.image.pull()

        kw_args = _CommandDict(self.info).build()
        kw_args['detach'] = True

        self.__container = self.__client.containers.run(self.info.image, **kw_args)
        LOGGER.debug("Ran container: %s", self.info.name)

    def restart(self) -> None:
        """Restarts a container."""
        self.stop()
        self.start()

    def start(self) -> None:
        """Starts a container.

        Notes:
            The container is started in daemonized (background, detached)
            mode.
        """
        LOGGER.debug("Starting container: %s", self.info.name)
        self.__get()
        if not self.__container:
            self.run()
        else:
            self.__container.start()
        LOGGER.debug("Started container: %s", self.info.name)

    def stop(self) -> None:
        """Stops a running container."""
        LOGGER.debug("Stopping container: %s", self.info.name)
        self.__get()
        self.__container.stop()
        LOGGER.debug("Stopped container: %s", self.info.name)

    def tag(self, img_tag: str) -> None:
        """Set the tag for this containers image.

        Args:
            img_tag: Tag to set for this image.
        """
        LOGGER.debug("Setting tag for container: %s", self.info.name)
        self.__get()
        self.info.tag = img_tag
        if self.file_p:
            _save_container_file(self.info.name, self.file_p, self.info.to_dict())

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
    def __init__(self, client: docker.DockerClient, config_path: str, groups: DockerGroups = None) -> None:
        self.__client = client
        self.__config_path = os.path.join(os.path.abspath(config_path), 'containers')
        fops.mkdir(self.__config_path)
        self.__containers = self.__list_defined()
        self.__groups = groups

    def __list_defined(self) -> dict:
        LOGGER.debug('Building a list of currently defined containers.')
        containers = dict()
        c_list = os.listdir(self.__config_path)

        for container_file in c_list:
            if container_file[-5:] == '.yaml':
                file_p = os.path.join(self.__config_path, container_file)
                containers[container_file[:-5]] = file_p

        return containers

    def define(self, container_def: str) -> str:
        """Adds a container via a container definition file

        Args:
            container_def: Definition file to use for adding a container.

        Returns:
            Name of newly defined container
        """
        LOGGER.debug("Reading container definition %s'", container_def)
        file_d = fops.file_read_convert(container_def, 'YAML')

        LOGGER.debug("Validating container definition %s", container_def)
        c_opts = self.validate_container_options(file_d)

        if c_opts['name'] in self.__containers:
            err_s = "Container '{0!s}' already defined.".format(c_opts['name'])
            raise DockerError(err_s)

        if self.__groups and c_opts['group']:
            if c_opts['group'] not in self.__groups.list():
                err_s = _ERR_CONTAINER_UNDEF_GROUP.format(c_opts['name'])
                raise ConfigError(err_s)
            g_info = self.__groups.get(c_opts['group'])
            if c_opts['name'] not in g_info.members:
                g_info.members.append(c_opts['name'])
                self.__groups.save()

        self.__containers[c_opts['name']] = os.path.join(self.__config_path, "{0!s}.yaml".format(c_opts['name']))

        _save_container_file(c_opts['name'], self.__containers[c_opts['name']], c_opts.to_dict())

        return c_opts.name

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

        LOGGER.debug("Reading container info for %s", container_name)
        file_d = fops.file_read_convert(self.__containers[container_name], 'YAML')

        LOGGER.debug("Validating container info for %s", container_name)
        container_info = self.validate_container_options(file_d)

        LOGGER.debug("Initializing image class for %s", container_name)
        container_image = DockerImage(self.__client, container_info.image,
                                      build_path=container_info.image_build_path,
                                      build_squash=container_info.image_build_squash,
                                      insecure_registry=container_info.image_insecure,
                                      username=container_info.image_username,
                                      password=container_info.image_password)

        return DockerContainer(self.__client, container_info, container_image, file_p=self.__containers[container_name])

    def list(self) -> list:
        """Returns a list of currently defined containers.

        Returns:
            A list of currently defined containers.
        """
        return [*self.__containers]

    @staticmethod
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
        for key in validated.keys():
            if key in options:
                data = options[key]
                if isinstance(data, (bytes, str)):
                    data = fops.makestr(data)
                validated.set_with_type(key, data)

        if not validated.image:
            raise ConfigError("'image' not defined in container options.")
        if not validated.name:
            raise ConfigError("'name' not defined in container options.")

        return validated
