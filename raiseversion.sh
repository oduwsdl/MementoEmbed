#!/bin/bash

# Update version in project
VERSION_STRING=`date -u +0.%Y.%m.%d.%H%M%S`
FILE_NAME='mementoembed/version.py'
DOC_FILE_NAME='mementoembed/docs/config.py'

# Update mementoembed version
sed -i.bak "s/^__appversion__ = .*$/__appversion__ = '$VERSION_STRING'/g" $FILE_NAME
sed -i.bak "s/^release = '.*'$/release = '$VERSION_STRING'/g"
