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
# group.py : Docker Groups
"""ElJef Docker Groups operations.

This module holds functionality for performing operations on Docker Groups.
"""
import logging
import os

from eljef.core import fops
from eljef.core.check import version_check
from eljef.core.dictobj import DictObj

from eljef.docker.exceptions import DockerError

LOGGER = logging.getLogger(__name__)

version_check(3, 6)


class DockerGroup(DictObj):
    """Docker group information class.

    Args:
        group_data: ``master`` and ``members`` data for the group.
    """
    def __init__(self, group_data: dict = None) -> None:
        super().__init__()
        self.master = None
        self.members = []
        if group_data and 'master' in group_data and group_data['master']:
            if not isinstance(group_data['master'], str):
                err_s = "'master' key in 'group_data' needs to be a str"
                raise TypeError(err_s)
            self.master = group_data['master']
        if group_data and 'members' in group_data and group_data['members']:
            if not isinstance(group_data['members'], list):
                err_s = "'members' key in 'group_data' needs to be a list"
                raise TypeError(err_s)
            self.members += group_data['members']


class DockerGroups(object):
    """Information class for groups of docker containers.

    config_path: Path to base configuration directory.
    """
    def __init__(self, config_path) -> None:
        fops.mkdir(os.path.abspath(config_path))
        self.__config = os.path.join(os.path.abspath(config_path),
                                     'groups.yaml')
        self.__groups = DictObj()
        self.__read()

    def __read(self) -> None:
        LOGGER.debug('Building list of currently defined groups.')
        groups_yaml = fops.file_read_convert(self.__config, 'YAML', True)
        for key, value in groups_yaml.items():
            self.add(key, value, False)

    def add(self, group: str, group_data: dict = None,
            save: bool = True) -> None:
        """Define a new group by name.

        Args:
            group: Name of group to define and add to the list of currently defined groups.
            group_data: `master` and `member` data for a group.
            save: Save group data to file after completion of adding.
        """
        if group not in self.__groups:
            self.__groups[group] = DockerGroup(group_data)
            if save:
                self.save()
            LOGGER.debug("Group '%s' successfully added.", group)
        else:
            LOGGER.debug("Group '%s' already exists.", group)

    def get(self, group) -> DockerGroup:
        """Get a group object by name.

        Args:
            group: Name of group to return group object for.

        Returns:
            Filled DockerGroup information class.

        Raises:
            DockerError: If group is not defined.
        """
        if group not in self.__groups:
            raise DockerError("Group '{0!s}' not defined.".format(group))

        return self.__groups[group]

    def list(self) -> list:
        """List defined groups.

        Returns:
            A list of defined groups. If there are no groups, am empty list is returned.
        """
        ret = []
        if self.__groups:
            ret += [*self.__groups]
        return ret

    def save(self) -> None:
        """Save group information to file."""
        LOGGER.debug('Saving groups information.')
        fops.file_write_convert(self.__config, 'YAML', self.__groups.to_dict())
