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
# __container__.py : CLI functions for ElJef Docker Containers
"""ElJef Docker CLI Container Functions

CLI functions for ElJef Docker Containers.
"""
import logging
import argparse

from eljef.core.check import version_check
from eljef.docker.cli.__vars__ import (CONFIG_PATH, PROJECT_NAME)
from eljef.docker.docker import Docker
from eljef.docker.exceptions import (ConfigError, DockerError)

LOGGER = logging.getLogger(__name__)

version_check(3, 6)


def container_define(definition_file: str) -> None:
    """Define a new container

    Args:
        definition_file: Path to container definition file.
    """
    LOGGER.info("Defining New Container")
    try:
        client = Docker(CONFIG_PATH)
        container_name = client.containers.define(definition_file)
        LOGGER.info("Defined New Container: %s", container_name)
    except ConfigError as err:
        LOGGER.error("Configuration Error: %s", err.message)
        raise SystemExit(1)
    except DockerError as err:
        LOGGER.error("Docker Error: %s", err.message)
        raise SystemExit(1)


def container_dump(container_name: str) -> None:
    """Dumps a containers definition file to the current directory.

    Args:
        container_name: Name of container.
    """
    LOGGER.info("Dumping container definition for '%s'", container_name)

    try:
        client = Docker(CONFIG_PATH)
        container = client.containers.get(container_name)
        definition_file = container.dump()
        LOGGER.info("Wrote container definition: %s", definition_file)
    except DockerError as err:
        LOGGER.error("Docker Error: %s", err.message)
        raise SystemExit(1)


def container_restart(container_name: str) -> None:
    """Restarts a defined container.

    Args:
        container_name: Name of container to start.
    """
    LOGGER.info("Restarting Container: '%s'", container_name)
    try:
        client = Docker(CONFIG_PATH)
        container = client.containers.get(container_name)
        container.restart()
        LOGGER.info("Restarted Container: '%s'", container_name)
    except DockerError as err:
        LOGGER.error("Docker Error: %s", err.message)
        raise SystemExit(-1)


def container_start(container_name: str) -> None:
    """Starts a defined container.

    Args:
        container_name: Name of container to start.
    """
    LOGGER.info("Starting Container: '%s'", container_name)

    try:
        client = Docker(CONFIG_PATH)
        container = client.containers.get(container_name)
        container.start()
        LOGGER.info("Started Container: '%s'", container_name)
    except DockerError as err:
        LOGGER.error("Docker Error: %s", err.message)
        raise SystemExit(-1)


def container_update(container_name: str) -> None:
    """Updates a containers image and rebuilds the container.

    Args:
        container_name: Name of container to update and rebuild.
    """
    LOGGER.info("Updating Container: %s", container_name)

    try:
        client = Docker(CONFIG_PATH)
        container = client.containers.get(container_name)
        container.update()
        container.rebuild()
        LOGGER.info("Updated Container: %s", container_name)
    except DockerError as err:
        LOGGER.error("Docker Error: %s", err.message)
        raise SystemExit(-1)


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


# noinspection PyUnresolvedReferences
def do_container(args: argparse.Namespace) -> None:
    """Runs container operations"""
    if args.container_define:
        container_define(args.container_define)
    elif args.container_dump:
        container_dump(args.container_dump)
    elif args.container_start:
        container_start(args.container_start)
    elif args.container_restart:
        container_restart(args.container_restart)
    elif args.container_update:
        container_update(args.container_update)
    elif args.containers_list:
        containers_list()
    else:
        LOGGER.error("You must specify an action. Try %s container --help", PROJECT_NAME)
        raise SystemExit(1)
