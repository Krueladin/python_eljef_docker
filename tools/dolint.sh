#!/usr/bin/env bash

flake8 eljef/docker/*.py eljef/docker/cli/*.py
pylint eljef/docker/*.py eljef/docker/cli/*.py
