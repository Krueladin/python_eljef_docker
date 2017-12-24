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
# group.py : Docker Exceptions
"""ElJef Docker Exceptions.

This module holds exceptions for the ElJef Docker module.
"""
import logging

from eljef.core.check import version_check

LOGGER = logging.getLogger(__name__)

version_check(3, 6)


class ConfigError(Exception):
    """Container configuration error class.

    Args:
        message: Error message
    """
    def __init__(self, message: str=None) -> None:
        Exception.__init__(self, message)
        self.message = message


class DockerError(Exception):
    """Docker error class.

    Args:
        message: Error Message
    """
    def __init__(self, message: str=None) -> None:
        Exception.__init__(self, message)
        self.message = message
