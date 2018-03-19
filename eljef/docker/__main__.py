# -*- coding: UTF-8 -*-
# pylint: disable=too-many-branches
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
# __main__.py : The main script for ElJef Docker operations
"""ElJef Docker Main

The main script for ElJef Docker operations.
"""
from typing import List
from typing import Tuple
from typing import Union

import logging
import argparse
import os
import platform

from eljef.core.applog import setup_app_logging
from eljef.core.check import version_check
from eljef.docker.containers import DockerContainer
from eljef.docker.docker import Docker
from eljef.docker.exceptions import DockerError
from eljef.docker.group import DockerGroup

LOGGER = logging.getLogger(__name__)

version_check(3, 6)

if platform.system() == 'Windows':
    CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.eljef', 'docker')
else:
    CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.config', 'eljef',
                               'docker')

C_LINE_ARGS = {
    '--container-define': {
        'dest': 'container_define',
        'metavar': 'CONTAINER_DEFINITION.YAML',
        'help': 'Define a new container using specified YAML definition file.'
    },
    '--container-dump': {
        'dest': 'container_dump',
        'metavar': 'CONTAINER_NAME',
        'help': 'Dumps a containers definition file to the current directory.'
    },
    '--container-start': {
        'dest': 'container_start',
        'metavar': 'CONTAINER_NAME',
        'help': 'Starts the defined container.'
    },
    '--container-update': {
        'dest': 'container_update',
        'metavar': 'CONTAINER_NAME',
        'help': 'Update the specified containers image and rebuild the '
                'container.'
    },
    '--containers-list': {
        'dest': 'containers_list',
        'action': 'store_true',
        'help': 'Returns a list of containers managed by the ElJef Docker '
                'software.'
    },
    '--group-define': {
        'dest': 'group_define',
        'metavar': 'GROUP_NAME',
        'help': 'Define new container group.'
    },
    '--group-info': {
        'dest': 'group_info',
        'metavar': 'GROUP_NAME',
        'help': 'Returns group information for the specified group.'
    },
    '--group-set-master': {
        'dest': 'group_set_master',
        'metavar': 'GROUP_NAME,MASTER_NAME',
        'help': 'Sets the master for the specified group. (This must be '
                'comma separated group_name,master_name)'
    },
    '--group-restart': {
        'dest': 'group_restart',
        'metavar': 'GROUP_NAME',
        'help': 'Restarts the specified group of containers.'
    },
    '--group-start': {
        'dest': 'group_start',
        'metavar': 'GROUP_NAME',
        'help': 'Starts the specified group of containers.'
    },
    '--group-stop': {
        'dest': 'group_stop',
        'metavar': 'GROUP_NAME',
        'help': 'Stops all containers in the specified group.'
    },
    '--group-update': {
        'dest': 'group_update',
        'metavar': 'GROUP_NAME',
        'help': 'Update all containers in the specified group and rebuild '
                'them.'
    },
    '--groups-list': {
        'dest': 'groups_list',
        'action': 'store_true',
        'help': 'Returns a list of currently defined groups.'
    }
}


def _group_get(client: Docker, group_name: str) -> DockerGroup:
    try:
        group = client.groups.get(group_name)
        return group
    except DockerError as err:
        LOGGER.error(err.message)
        raise SystemExit(-1)


def _group_list(client: Docker,
                group: DockerGroup) -> Tuple[DockerContainer,
                                             List[DockerContainer]]:
    master = None
    if group.master:
        master = client.containers.get(group.master)

    containers = []
    for container_name in group.members:
        if container_name != group.master:
            containers.append(client.containers.get(container_name))

    return master, containers


def _group_start(master: Union[DockerContainer, None],
                 containers: List[DockerContainer]) -> None:
    update_s = "Starting new copy of container '%s'"
    if master:
        LOGGER.info(update_s, master.info.name)
        master.start()
    for container in containers:
        LOGGER.info(update_s, container.info.name)
        container.start()


def _group_stop(master: Union[DockerContainer, None],
                containers: List[DockerContainer],
                remove: bool = False) -> None:
    update_s = "Shutting down container '{0!s}'"
    if remove:
        update_s = "Shutting down and removing container '%s'"
    for container in containers:
        LOGGER.info(update_s, container.info.name)
        container.stop()
        if remove:
            container.remove()
    if master:
        LOGGER.info(update_s, master.info.name)
        master.stop()
        if remove:
            master.remove()


def container_define(definition_file: str) -> None:
    """Define a new container

    Args:
        definition_file: Path to container definition file.
    """
    LOGGER.info("Defining New Container")

    client = Docker(CONFIG_PATH)
    container_name = client.containers.define(definition_file)

    LOGGER.info("Defined New Container: %s", container_name)


def container_dump(container_name: str) -> None:
    """Dumps a containers definition file to the current directory.

    Args:
        container_name: Name of container.
    """
    LOGGER.info("Dumping container definition for '%s'", container_name)

    client = Docker(CONFIG_PATH)
    container = client.containers.get(container_name)
    definition_file = container.dump()

    LOGGER.info("Wrote container definition: %s", definition_file)


def container_start(container_name: str) -> None:
    """Starts a defined container.

    Args:
        container_name: Name of container to start.
    """
    LOGGER.info("Starting Container: '%s'", container_name)

    client = Docker(CONFIG_PATH)
    try:
        container = client.containers.get(container_name)
        container.start()
        LOGGER.info("Started Container: '%s'", container_name)
    except DockerError as err:
        LOGGER.error(err.message)
        raise SystemExit(-1)


def container_update(container_name: str) -> None:
    """Updates a containers image and rebuilds the container.

    Args:
        container_name: Name of container to update and rebuild.
    """
    LOGGER.info("Updating Container: %s", container_name)

    client = Docker(CONFIG_PATH)
    container = client.containers.get(container_name)

    container.update()
    container.rebuild()

    LOGGER.info("Updated Container: %s", container_name)


def containers_list() -> None:
    """Returns a list of currently defined containers."""
    client = Docker(CONFIG_PATH)
    containers = client.containers.list()

    if containers:
        LOGGER.info('Currently Defined Containers:')
        for container in sorted(containers):
            LOGGER.info("    %s", container)
    else:
        LOGGER.info('No Currently Defined Containers')


def group_define(group_name: str) -> None:
    """Define a new container group

    Args:
        group_name: Name of group to define.
    """
    LOGGER.info("Defining Group: %s", group_name)

    client = Docker(CONFIG_PATH)
    client.groups.add(group_name)

    LOGGER.info("Defined Group: %s", group_name)


def group_info(group_name: str) -> None:
    """Returns information for `group_name`

    Args:
        group_name: Group name to retrieve information for.
    """
    client = Docker(CONFIG_PATH)
    try:
        group = client.groups.get(group_name)
    except DockerError as err:
        LOGGER.error(err.message)
        raise SystemExit(-1)

    LOGGER.info("Group: %s", group_name)
    if group.master:
        LOGGER.info("    Master: %s", group.master)
    if len(group.members) <= 0:
        LOGGER.info("    Members: None Defined.")
    else:
        LOGGER.info("    Members:")
        for member_name in sorted(group.members):
            LOGGER.info("        %s", member_name)


def group_set_master(group_name: str, master_name: str) -> None:
    """Sets `group_names` master to `master_name`

    Args:
        group_name: Name of group to set master of.
        master_name: Name of container to set as master for group.
    """
    LOGGER.info("Setting master of '%s' to '%s'", group_name, master_name)
    client = Docker(CONFIG_PATH)
    group = client.groups.get(group_name)
    containers = client.containers.list()

    if master_name not in containers:
        LOGGER.error("Specified master_name '%s' is not defined.", master_name)
        raise SystemExit(-1)

    group.master = master_name
    client.groups.save()

    LOGGER.info("Set master of '%s' to '%s'", group_name, master_name)


def group_start(group_name: str) -> None:
    """Starts the specified group of containers.

    Args:
        group_name: Group name to start.
    """
    client = Docker(CONFIG_PATH)
    group = _group_get(client, group_name)
    master, containers = _group_list(client, group)

    LOGGER.info("Starting Containers Group: '%s'", group_name)
    _group_start(master, containers)
    LOGGER.info("Finished updating and rebuilding members of group '%s'",
                group_name)


def group_stop(group_name: str) -> None:
    """Stops all containers in the specified group.

    Args:
        group_name: Group name to stop.
    """
    client = Docker(CONFIG_PATH)
    group = _group_get(client, group_name)
    master, containers = _group_list(client, group)

    LOGGER.info("Stopping Containers Group: '%s'", group_name)
    _group_stop(master, containers)
    LOGGER.info("Stopped Containers Group: '%s'", group_name)


def group_update(group_name: str) -> None:
    """Updates all containers in a group and rebuilds them.

    Args:
        group_name: Group name to update and rebuild.
    """
    client = Docker(CONFIG_PATH)
    group = _group_get(client, group_name)
    master, containers = _group_list(client, group)

    LOGGER.info("Updating and rebuilding members of group '%s'", group_name)

    if master:
        LOGGER.info("Updating container image for '%s'", master.info.name)
        master.image.pull()
    for container in containers:
        LOGGER.info("Updating container image for '%s'", container.info.name)
        container.image.pull()

    _group_stop(master, containers, True)

    _group_start(master, containers)

    LOGGER.info("Finished updating and rebuilding members of group '%s'",
                group_name)


def groups_list() -> None:
    """Returns a list of currently defined groups."""
    client = Docker(CONFIG_PATH)
    groups = client.groups.list()

    if groups:
        LOGGER.info('Currently Defined Groups:')
        for group in groups:
            LOGGER.info("    %s", group)
    else:
        LOGGER.info('No Currently Defined Groups')


# noinspection PyUnresolvedReferences
def main() -> None:
    """Main function"""
    project_desc = 'ElJef Docker functionality'
    parser = argparse.ArgumentParser(description=project_desc)

    for key, value in C_LINE_ARGS.items():
        parser.add_argument(key, **value)

    parser.add_argument('--debug', dest='debug_log', action='store_true',
                        help='Enable debug output.')

    args = parser.parse_args()
    setup_app_logging(args.debug_log)

    if args.container_define:
        container_define(args.container_define)
    elif args.container_dump:
        container_dump(args.container_dump)
    elif args.container_start:
        container_start(args.container_start)
    elif args.container_update:
        container_update(args.container_update)
    elif args.containers_list:
        containers_list()
    elif args.group_define:
        group_define(args.group_define)
    elif args.group_info:
        group_info(args.group_info)
    elif args.group_set_master:
        group_name, master_name = args.group_set_master.split(',')
        group_set_master(group_name, master_name)
    elif args.group_start:
        group_start(args.group_start)
    elif args.group_stop:
        group_stop(args.group_stop)
    elif args.group_update:
        group_update(args.group_update)
    elif args.groups_list:
        groups_list()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
