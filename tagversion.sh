#!/bin/bash

VERSION_STRING=`date -u +0.%Y%m%d%H%M%S`

./raiseversion.sh $VERSION_STRING

modified_files=`git status | grep modified | sed 's/^.*modified:[ ]*//g'`

found_mods=0

for fname in ${modified_files}; do

    if [ ${fname} == "docs/source/conf.py" ]; then
        found_mods=`expr $found_mods + 1`
    fi

    if [ ${fname} != "mementoembed/version.py" ]; then
        found_mods=`expr $found_mods + 1`
    fi

done

if [ $found_mods != 2 ]; then
    echo "additional modified files need to be committed before tagging, run 'git status' to view them, then add and commit them"
    exit 22
fi

git add docs/source/conf.py
git add mementoembed/version.py
git commit -m "committing version ${VERSION_STRING} before taggin"

git tag -a v${VERSION_STRING} -m "tagging version v${VERSION_STRING}"
