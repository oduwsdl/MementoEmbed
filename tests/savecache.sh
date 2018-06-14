#!/bin/bash

# Thanks: https://stackoverflow.com/questions/59895/getting-the-source-directory-of-a-bash-script-from-within
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "my directory is $DIR"

cd /tmp/mementoembed/
tar cvfj testcache.tar.bz2 test_mementosurrogate.py
cp testcache.tar.bz2 "${DIR}"
