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
# __private.py: Internal functionality to eljef.docker
import logging

from typing import Tuple
from typing import Union

from eljef.core import fops
from eljef.core.check import version_check

LOGGER = logging.getLogger(__name__)

version_check(3, 6)

DOCKER_INFO = {
    'config_path': None,
    'containers': {},
    'files': {
        'containers': None,
        'groups': None
    },
    'host': None,
    'groups': {}
}

DOCKER_OPTS = {
    'cap_add': [],
    'cap_drop': [],
    'daemonize': True,
    'devices': [],
    'dns': [],
    'environment': [],
    'group': None,
    'image': None,
    'image_args': [],
    'mounts': [],
    'name': None,
    'net': None,
    'network': None,
    'ports': [],
    'restart': None
}

DOCKER_OPTS_TYPES = {
    'cap_add': list,
    'cap_drop': list,
    'daemonize': bool,
    'devices': list,
    'dns': list,
    'environment': list,
    'group': str,
    'image': str,
    'image_args': list,
    'mounts': list,
    'name': str,
    'net': str,
    'network': str,
    'ports': list,
    'restart': str
}

DOCKER_OPTS_LIST_KEYS = {
    'cap-add',
    'cap-drop',
    'devices',
    'dns',
    'environment',
    'image_args',
    'mounts',
    'ports'
}

DOCKER_OPTS_REQUIRED = {'image', 'name'}

VALIDATE_TE = "Incorrect key type: '{0!s}' is '{1!s}' but needs to be '{2!s}'"
VALIDATE_TE_LIST = "Incorrect list contents: Value at position '{0!s}' in "\
                   "key '{1!s} has a type of '{2!s}' when it should be 'str'"


class ContainerOpts(dict):
    """Storage class for docker run options."""
    def __getattr__(self, attr):
        return self[attr]

    def __setattr__(self, attr, value):
        self[attr] = value


def get_container_opts() -> ContainerOpts:
    """Returns a ContainerOpts storage holder with all defaults pre-filled.

    Returns:
        ContainerOpts storage holder

    Note:
        key: type as follows
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
    """
    d = ContainerOpts()
    d.update(DOCKER_OPTS)
    return d


def get_docker_info() -> ContainerOpts:
    """Returns a ContainerOpts storage holder for the main docker class.

    Returns:
        ContainerOpts storage holder
    """
    d = ContainerOpts()
    d.update(DOCKER_INFO)
    return d


def validate_option_types(options: dict) -> Tuple[bool,
                                                  Union[str, None],
                                                  ContainerOpts]:
    """Validate incoming option types to provide base sanity

    Args:
        options: Dictionary of options to be used with docker. (Typically fed
                 from a YAML config file.

    Returns:
        A tuple as follows.
        Position 1: Error Condition: False if no error, True if error.
        Position 2: Error String: Description of error.
        Position 3: Validated Options: ContainerOpts class containing type
                                       validated options.
   """
    err = False
    err_s = None
    validated = get_container_opts()
    for key in validated:
        if key in options:
            data = options[key]
            if type(data) in {bytes, str}:
                data = fops.makestr(data)
            if type(data) != DOCKER_OPTS_TYPES[key]:
                k_is = type(data).__name__
                k_sb = DOCKER_OPTS_TYPES[key].__name__
                err_s = VALIDATE_TE.format(key, k_is, k_sb)
                err = True
                break
            validated[key] = data

    if not err:
        for key in DOCKER_OPTS_LIST_KEYS:
            c = 0
            new_list = []
            old_list = validated[key]
            while c < len(old_list):
                if type(old_list[c]) not in {bytes, str}:
                    k_is = type(old_list[c]).__name__
                    err_s = VALIDATE_TE_LIST.format(c, key, k_is)
                    err = True
                    break
                new_list.append(fops.makestr(old_list[c]))
            if not err:
                validated[key] = new_list

    return err, err_s, validated


def validate_container_options(options: ContainerOpts) -> Tuple[bool,
                                                                Union[str,
                                                                      None]]:
    """Validates options in a container definition.

    Args:
        options: ContainerOpts of options from a container definition.

    Returns:
        A tuple as follows.
        Position 1: Error Condition: False if no error, True if error.
        Position 2: Error String: Description of error.
    """
    err = False
    err_s = None
    for check in DOCKER_OPTS_REQUIRED:
        if check not in options:
            err = True
            err_s = "Container definition missing '{0!s}' key".format(check)
            break

    return err, err_s
