#!/bin/bash

# git checkout master
# git pull

# Update version in project
PYVAR="__appversion__ = "
VERSION_STRING=`date -u +0.%Y.%m.%d.%H%M`
FILE_NAME='mementoembed/version.py'

# Update mementoembed version
# echo $PYVAR\'$VERSION_STRING\'>'mementoembed/'$FILE_NAME
sed -i.bak  "s/^__appversion__ = .*$/__appversion__ = '$VERSION_STRING'/g" $FILE_NAME

# uncomment below when ready

# Push to GitHub
# git add 'ipwb/'$FILE_NAME
# git commit -m "RELEASE: Bump version for pypi to "$VERSION_STRING

# Create a tag in repo
TAG_NAME='v'$VERSION_STRING
# git tag $TAG_NAME
# git push
# git push origin $TAG_NAME
