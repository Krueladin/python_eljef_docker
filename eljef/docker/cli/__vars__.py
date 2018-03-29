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
# __vars__.py : Variables used by ElJef Docker CLI
"""ElJef Docker Variables

Variables used by ElJef Docker CLI.
"""
import logging
import os
import platform
import sys

from eljef.core.check import version_check
from eljef.docker.__version__ import VERSION as EJD_VERSION

LOGGER = logging.getLogger(__name__)

version_check(3, 6)

if platform.system() == 'Windows':
    CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.eljef', 'docker')
else:
    CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.config', 'eljef', 'docker')

PROJECT_DESCRIPTION = 'ElJef Docker functionality'
PROJECT_NAME = os.path.basename(sys.argv[0])
PROJECT_VERSION = EJD_VERSION
