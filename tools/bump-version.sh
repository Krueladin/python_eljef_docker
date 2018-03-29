#!/usr/bin/env bash

if [ -z "$1" ]; then
    echo "bump-version.sh new_version"
    exit 1
fi

sed -e "s/VERSION = .*$/VERSION = '${1}'/" \
    -i eljef/docker/__version__.py
sed -e "s/version = .*$/version = '${1}'/" \
    -e "s/release = .*$/release = '${1}'/" \
    -i docs/source/conf.py
sed -e "s/version=.*,/version='${1}',/" \
    -i setup.py
