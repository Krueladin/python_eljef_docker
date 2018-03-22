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
import logging
import argparse
import sys

from eljef.core.applog import setup_app_logging
from eljef.core.check import version_check
from eljef.docker.cli.__opts__ import C_LINE_ARGS
from eljef.docker.cli.__vars__ import PROJECT_DESCRIPTION

LOGGER = logging.getLogger(__name__)

version_check(3, 6)


def main() -> None:
    """Main function"""
    parser = argparse.ArgumentParser(description=PROJECT_DESCRIPTION)
    parser.add_argument('--debug', dest='debug_log', action='store_true',
                        help='Enable debug output.')
    subparsers = parser.add_subparsers(help='command help')

    for sub, opts in C_LINE_ARGS.items():
        sub_parser = subparsers.add_parser(sub, help=opts['help'])
        for op_name, args in opts['ops'].items():
            sub_parser.add_argument(op_name, **args)
            sub_parser.set_defaults(func=opts['func'])

    args = parser.parse_args()
    setup_app_logging(args.debug_log)

    has_sub = False
    for sub in C_LINE_ARGS:
        if sub in sys.argv:
            has_sub = True
            break

    if not has_sub:
        parser.print_help()
        raise SystemExit(1)

    args.func(args)


if __name__ == "__main__":
    main()
