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
# docker.py : Docker operations
"""ElJef Docker operations.

This module holds functionality for performing operations on Docker containers.
"""
import copy
import logging
import os

from eljef.core import fops
from eljef.core.check import version_check
from eljef.docker.__private import ContainerOpts
from eljef.docker.__private import get_docker_info as _get_docker_info
from eljef.docker.__private import validate_option_types as \
    _validate_option_types
from eljef.docker.__private import validate_container_options as \
    _validate_container_options

LOGGER = logging.getLogger(__name__)

version_check(3, 6)


def validate_container_options(options: dict) -> ContainerOpts:
    """Validate incoming option types to provide base sanity

    Args:
        options: Dictionary of options to be used with docker. (Typically fed
                 from a YAML config file.

    Returns:
        A ContainerOpts object holding the configuration options for a
        docker container.

    Note:
        The returned ContainerOpts object contents can be retrieved via
        dictionary and object attribute methods.
        ie:
            obj['key']
            obj.key
        The returned ContainerOpts object is keyed as follows:
        key: type
            cap_add: list[str]
            cap_drop: list[str]
            daemonize: bool
            devices: list[str]
            dns: list[str]
            environment: list[str]
            group: str
            image: str
            image_args: list[str]
            mounts: list[str]
            name: str
            net: str
            network: str
            ports: list[str]
            restart: str

    Raises:
        TypeError: If type type of data in a key provided in ``options``
                   doesn't match the required type.
    """
    err, err_s, validated = _validate_option_types(options)
    if err:
        raise TypeError(err_s)
    err, err_s = _validate_container_options(validated)
    if err:
        raise ValueError(err_s)

    return validated


class ConfigError(Exception):
    """Container configuration error class.

    Args:

    """
    def __init__(self, message):
        Exception.__init__(self, message)
        self.message = message


class Docker(object):
    """Docker information and control class.

    Args:
        config_path: Path to base configuration directory.
        host: If the host running dockerd is remote, the hostname must should
              be provided in [hostname/ip]:port format.
    """
    def __init__(self, config_path: str, host: str=None) -> None:
        self.__info = _get_docker_info()
        cp = os.path.abspath(config_path)
        self.__info['config_path'] = cp
        self.__info['host'] = host
        self.__info['files']['containers'] = os.path.join(cp, 'containers')
        self.__info['files']['groups'] = os.path.join(cp, 'groups.yaml')
        self.__read_groups()
        self.__build_container_list()

    def __build_container_list(self):
        LOGGER.debug('Building a list of currently defined containers.')
        c_list = os.listdir(self.__info['files']['containers'])
        for container in c_list:
            fp = os.path.join(self.__info['files']['containers'], container)
            self.container_add(fp, False)

    def __get_group_info(self, group: str) -> dict:
        LOGGER.debug("Getting group information for {0!s}".format(group))

        if group not in self.__info['groups']:
            err_s = "Group '{0!s}' not in defined groups.".format(group)
            raise ValueError(err_s)

        return self.__info['groups'][group]

    def __read_groups(self):
        LOGGER.debug('Building list of currently defined groups.')
        gf = self.__info['files']['groups']
        t = fops.file_read_convert(gf, 'YAML', True)
        self.__info['groups'].update(t)

    def __save_groups(self):
        LOGGER.debug('Saving groups information.')
        fops.file_write_convert(self.__info['files']['groups'],
                                'YAML', self.__info['groups'])

    def container_add(self, container_def: str, save_def: bool=True) -> None:
        """Adds a container via a container definition file

        Args:
            container_def: Definition file to use for adding a container.
            save_def: Save the configuration. (Default is True)
        """
        fd = fops.file_read_convert(container_def, 'YAML')
        t = validate_container_options(fd)

        LOGGER.debug("Reading container '{0!s}'".format(t['name']))

        if t['group']:
            if t['group'] not in self.__info['groups']:
                err_s = "Container definition for '{0!s}' contains " \
                        "group that is not defined. " \
                        "Add group first.".format(t['name'])
                raise ConfigError(err_s)
            if t['name'] not in self.__info['groups'][t['group']]['members']:
                self.__info['groups'][t['group']]['members'].append(t['name'])
                self.__save_groups()

        fp = os.path.join(self.__info['files']['containers'], t['name'])
        self.__info['containers'][t['name']] = fp

        if save_def:
            LOGGER.debug("Saving configuration for '{0!s}'")
            fops.file_write_convert(fp, 'YAML', t)

    def group_add(self, group) -> None:
        """Define a new group by name.

        Args:
            group: Name of group to define and add to the list of currently
                   defined groups.
        """
        if group in self.__info['groups']:
            err_s = "Group '{0!s} already defined.".format(group)
            raise ValueError(err_s)

        t = {'master': None, 'members': []}
        self.__info['groups'][group] = t
        self.__save_groups()

        LOGGER.info("Group '{0!s}' successfully added.".format(group))

    def group_list(self) -> list:
        """List defined groups.

        Returns:
            A list of defined groups. If there are no groups, am empty list is
            returned.
        """
        ret = []
        if len(self.__info['groups']) > 0:
            ret += [*self.__info['groups']]
        return ret

    def group_master(self, group: str) -> str:
        """Returns the master for the given ``group``

        Args:
            group: Group name to get master of.

        Returns:
            The name of the master of the specified ``group``.
        """
        group_info = self.__get_group_info(group)

        if 'master' not in group_info or not group_info['master']:
            err_s = "Group '{0!s}' has no defined master.".format(group)
            raise ValueError(err_s)

        return group_info['master']

    def group_master_set(self, group: str, master: str) -> None:
        """Sets the master for the given ``group``

        Args:
            group: Group name to set master for.
            master: Name of master to set for group.
        """
        group_info = copy.deepcopy(self.__get_group_info(group))
        group_info['master'] = master
        self.__info['groups'][group] = group_info
        self.__save_groups()

        log_s = "'{0!s}' set as master of group '{1!s}'".format(master, group)
        LOGGER.info(log_s)

    def group_members(self, group: str) -> str:
        """Returns the members of the given ``group``

        Args:
            group: Group name to get members of.

        Returns:
            List of members of the specified ``group``.
        """
        group_info = self.__get_group_info(group)

        ret = []
        if 'members' in group_info:
            ret = group_info['members']

        return ret
