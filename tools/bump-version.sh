#!/usr/bin/env bash

if [ -z "$1" ]; then
    echo "bump-version.sh [c |new_version]"
    echo ""
    echo "    c            get current version"
    echo "    new_version  new version to set"
    exit 1
elif [ "$1" == "c" ]; then
    cat eljef/docker/__version__.py | grep 'VERSION' | \
    sed -e 's/VERSION = //' -e "s/'//g"
fi

sed -e "s/VERSION = .*$/VERSION = '${1}'/" \
    -i eljef/docker/__version__.py
sed -e "s/version = .*$/version = '${1}'/" \
    -e "s/release = .*$/release = '${1}'/" \
    -i docs/source/conf.py
sed -e "s/version=.*,/version='${1}',/" \
    -i setup.py
