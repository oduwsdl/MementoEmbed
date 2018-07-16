#!/bin/bash

# Update version in project
VERSION_STRING=`date -u +0.%Y.%m.%d.%H%M`
FILE_NAME='mementoembed/version.py'

# Update mementoembed version
sed -i.bak  "s/^__appversion__ = .*$/__appversion__ = '$VERSION_STRING'/g" $FILE_NAME
