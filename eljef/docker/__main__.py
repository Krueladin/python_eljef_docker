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
# __main__.py : The main script for ElJef Docker operations
"""ElJef Docker Main

The main script for ElJef Docker operations.
"""

import argparse
import logging
import os
import platform
import sys

from eljef.core.check import version_check
from eljef.docker.docker import Docker
from eljef.docker.exceptions import DockerError

LOGGER = logging.getLogger(__name__)

version_check(3, 6)

if platform.system() == 'Windows':
    CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.eljef', 'docker')
else:
    CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.config', 'eljef',
                               'docker')


def define_container(definition_file: str) -> None:
    """Define a new container

    Args:
        definition_file: Path to container definition file.
    """
    LOGGER.info("Defining New Container")

    client = Docker(CONFIG_PATH)
    container_name = client.containers.define(definition_file)

    LOGGER.info("Defined New Container: {0!s}".format(container_name))


def define_group(group_name: str) -> None:
    """Define a new container group

    Args:
        group_name: Name of group to define.
    """
    LOGGER.info("Defining Group: {0!s}".format(group_name))

    client = Docker(CONFIG_PATH)
    client.groups.add(group_name)

    LOGGER.info("Defined Group: {0!s}".format(group_name))


def dump_container(container_name: str) -> None:
    """Dumps a containers definition file to the current directory.

    Args:
        container_name: Name of container.
    """
    log_s = "Dumping container definition for '{0!s}'"
    LOGGER.info(log_s.format(container_name))

    client = Docker(CONFIG_PATH)
    container = client.containers.get(container_name)
    definition_file = container.dump()

    log_s = "Wrote container definition: {0!s}"
    LOGGER.info(log_s.format(definition_file))


def group_info(group_name: str) -> None:
    """Returns information for `group_name`

    Args:
        group_name: Group name to retrieve information for.
    """
    client = Docker(CONFIG_PATH)
    try:
        group = client.groups.get(group_name)

        LOGGER.info("Group: {0!s}".format(group_name))
        if group.master:
            LOGGER.info("    Master: {0!s}".format(group.master))
        if len(group.members) <= 0:
            LOGGER.info("    Members: None Defined.")
        else:
            LOGGER.info("    Members:")
            for member_name in sorted(group.members):
                LOGGER.info("        {0!s}".format(member_name))

    except DockerError as e:
        LOGGER.error(e.message)


def list_containers() -> None:
    """Returns a list of currently defined containers."""
    client = Docker(CONFIG_PATH)
    containers = client.containers.list()

    if len(containers) > 0:
        LOGGER.info('Currently Defined Containers:')
        for container in sorted(containers):
            LOGGER.info("    {0!s}".format(container))
    else:
        LOGGER.info('No Currently Defined Containers')


def list_groups() -> None:
    """Returns a list of currently defined groups."""
    client = Docker(CONFIG_PATH)
    groups = client.groups.list()

    if len(groups) > 0:
        LOGGER.info('Currently Defined Groups:')
        for group in groups:
            LOGGER.info("    {0!s}".format(group))
    else:
        LOGGER.info('No Currently Defined Groups')


def set_group_master(group_name: str, master_name: str) -> None:
    """Sets `group_names` master to `master_name`

    Args:
        group_name: Name of group to set master of.
        master_name: Name of container to set as master for group.
    """
    log_s = "Settings master of '{0!s}' to '{1!s}'"
    LOGGER.info(log_s.format(group_name, master_name))
    client = Docker(CONFIG_PATH)
    group = client.groups.get(group_name)
    containers = client.containers.list()

    if master_name not in containers:
        err_s = "Specified master_name '{0!s}' is not defined."
        LOGGER.error(err_s.format(master_name))
        raise SystemExit(-1)

    group.master = master_name
    client.groups.save()

    log_s = "Set master of '{0!s}' to '{1!s}'"
    LOGGER.info(log_s.format(group_name, master_name))


def update_container(container_name: str) -> None:
    """Updates a containers image and rebuilds the container.

    Args:
        container_name: Name of container to update and rebuild.
    """
    LOGGER.info("Updating Container: {0!s}".format(container_name))

    client = Docker(CONFIG_PATH)
    container = client.containers.get(container_name)

    container.update()
    container.rebuild()

    LOGGER.info("Updated Container: {0!s}".format(container_name))


def update_group(group_name: str) -> None:
    """Updates all containers in a group and rebuilds them.

    Args:
        group_name: Group name to update and rebuild.
    """


def main() -> None:
    """Main function"""
    project_desc = 'ElJef Docker functionality'
    parser = argparse.ArgumentParser(description=project_desc)
    parser.add_argument('--define-container', dest='define_container',
                        help='Define a new container using specified YAML '
                             'definition file.')
    parser.add_argument('--define-group', dest='define_group',
                        help='Define new container group.')
    parser.add_argument('--dump-container', dest='dump_container',
                        help='Dumps a containers definition file to the '
                             'current directory.')
    parser.add_argument('--group-info', dest='group_info',
                        help='Returns group information for the specified '
                             'group.')
    parser.add_argument('--list-containers', dest='list_containers',
                        action='store_true',
                        help='Returns a list of containers managed by the '
                             'ElJef Docker software.')
    parser.add_argument('--list-groups', dest='list_groups',
                        action='store_true',
                        help='Returns a list of currently defined groups.')
    parser.add_argument('--set-group-master', dest='set_group_master',
                        help='Sets the master for the specified group. '
                             '(This must be comma separated '
                             'group_name,master_name)')
    parser.add_argument('--update-container', dest='update_container',
                        help='Update the specified containers image and '
                             'rebuild the container.')
    parser.add_argument('--update-group', dest='update_group',
                        help='Update all containers in the specified group and'
                             'rebuild them.')
    parser.add_argument('--debug', dest='debug_log', action='store_true',
                        help='Enable debug output.')
    args = parser.parse_args()

    LOGGER.setLevel(logging.DEBUG if args.debug_log else logging.INFO)
    c_formatter = logging.Formatter('%(message)s')
    c_handler = logging.StreamHandler(sys.stdout)
    c_handler.setLevel(logging.DEBUG if args.debug_log else logging.INFO)
    c_handler.setFormatter(c_formatter)
    LOGGER.addHandler(c_handler)

    if args.define_container:
        define_container(args.define_container)
    elif args.define_group:
        define_group(args.define_group)
    elif args.dump_container:
        dump_container(args.dump)
    elif args.group_info:
        group_info(args.group_info)
    elif args.list_containers:
        list_containers()
    elif args.list_groups:
        list_groups()
    elif args.set_group_master:
        group_name, master_name = args.set_group_master.split(',')
        set_group_master(group_name, master_name)
    elif args.update_container:
        update_container(args.update_container)
    elif args.update_group:
        update_group(args.update_group)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
