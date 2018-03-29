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
# __group__.py : CLI functions for ElJef Docker Groups
"""ElJef Docker CLI Group Functions

CLI functions for ElJef Docker Groups.
"""
from typing import List
from typing import Tuple
from typing import Union

import logging
import argparse

from eljef.core.check import version_check
from eljef.docker.cli.__vars__ import (CONFIG_PATH, PROJECT_NAME)
from eljef.docker.containers import DockerContainer
from eljef.docker.docker import Docker
from eljef.docker.exceptions import DockerError
from eljef.docker.group import DockerGroup

LOGGER = logging.getLogger(__name__)

version_check(3, 6)


def _group_get(client: Docker, group_name: str) -> DockerGroup:
    try:
        group = client.groups.get(group_name)
        return group
    except DockerError as err:
        LOGGER.error(err.message)
        raise SystemExit(-1)


def _group_list(client: Docker, group: DockerGroup) -> Tuple[DockerContainer, List[DockerContainer]]:
    master = None
    if group.master:
        master = client.containers.get(group.master)

    containers = []
    for container_name in group.members:
        if container_name != group.master:
            containers.append(client.containers.get(container_name))

    return master, containers


def _group_start(master: Union[DockerContainer, None], containers: List[DockerContainer]) -> None:
    update_s = "Starting new copy of container '%s'"
    if master:
        LOGGER.info(update_s, master.info.name)
        master.start()
    for container in containers:
        LOGGER.info(update_s, container.info.name)
        container.start()


def _group_stop(master: Union[DockerContainer, None], containers: List[DockerContainer], remove: bool = False) -> None:
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
    LOGGER.info("Finished updating and rebuilding members of group '%s'", group_name)


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

    LOGGER.info("Finished updating and rebuilding members of group '%s'", group_name)


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
def do_group(args: argparse.Namespace) -> None:
    """Runs group operations"""
    if args.group_define:
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
        LOGGER.error("You must specify an action. Try %s group --help",
                     PROJECT_NAME)
        raise SystemExit(1)
