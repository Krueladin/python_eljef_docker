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
# __opts__.py : CLI Arguments for ElJef Docker
"""ElJef Docker CLI Options

CLI Arguments for ElJef Docker
"""
import logging

from eljef.core.check import version_check
from eljef.docker.cli.__container__ import do_container
from eljef.docker.cli.__group__ import do_group

LOGGER = logging.getLogger(__name__)

version_check(3, 6)

C_LINE_ARGS = [
    {
        'short': '-d',
        'long': '--debug',
        'opts': {
            'dest': 'debug_log',
            'action': 'store_true',
            'help': 'Enable debug output.'
        }
    },
    {
        'short': '-v',
        'long': '--version',
        'opts': {
            'dest': 'version_out',
            'action': 'store_true',
            'help': 'Print version and exit.'
        }
    }
]

C_LINE_GROUPS = {
    'container': {
        'help': 'Operations to be performed on an individual containers.',
        'func': do_container,
        'ops': {
            '--list': {
                'dest': 'containers_list',
                'action': 'store_true',
                'help': 'Returns a list of containers managed by the ElJef Docker software.'
            },
            '--define': {
                'dest': 'container_define',
                'metavar': 'CONTAINER_DEFINITION.YAML',
                'help': 'Define a new container using specified YAML definition file.'
            },
            '--name': {
                'dest': 'container_name',
                'metavar': 'CONTAINER_NAME',
                'help': 'Container to perform action on.'
            },
            '--dump': {
                'dest': 'container_dump',
                'action': 'store_true',
                'help': 'Dumps a containers definition file to the current directory.'
            },
            '--start': {
                'dest': 'container_start',
                'action': 'store_true',
                'help': 'Starts the defined container.'
            },
            '--stop': {
                'dest': 'container_stop',
                'action': 'store_true',
                'help': "Stops the defined container."
            },
            '--restart': {
                'dest': 'container_restart',
                'action': 'store_true',
                'help': 'Restarts the defined container.'
            },
            '--update': {
                'dest': 'container_update',
                'action': 'store_true',
                'help': 'Update the specified containers image and rebuild the container.'
            },
            '--tag': {
                'dest': 'container_tag',
                'metavar': 'IMAGE_TAG',
                'help': 'Set or Update the tag for the specified containers image.'
            }
        }
    },
    'group': {
        'help': 'Operations to be performed on a group of containers.',
        'func': do_group,
        'ops': {
            '--define': {
                'dest': 'group_define',
                'metavar': 'GROUP_NAME',
                'help': 'Define new container group.'
            },
            '--info': {
                'dest': 'group_info',
                'metavar': 'GROUP_NAME',
                'help': 'Returns group information for the specified group.'
            },
            '--set-master': {
                'dest': 'group_set_master',
                'metavar': 'GROUP_NAME,MASTER_NAME',
                'help': 'Sets the master for the specified group. (This must be comma separated group_name,master_name)'
            },
            '--restart': {
                'dest': 'group_restart',
                'metavar': 'GROUP_NAME',
                'help': 'Restarts the specified group of containers.'
            },
            '--start': {
                'dest': 'group_start',
                'metavar': 'GROUP_NAME',
                'help': 'Starts the specified group of containers.'
            },
            '--stop': {
                'dest': 'group_stop',
                'metavar': 'GROUP_NAME',
                'help': 'Stops all containers in the specified group.'
            },
            '--update': {
                'dest': 'group_update',
                'metavar': 'GROUP_NAME',
                'help': 'Update all containers in the specified group and rebuild them.'
            },
            '--list': {
                'dest': 'groups_list',
                'action': 'store_true',
                'help': 'Returns a list of currently defined groups.'
            }
        }
    }
}
