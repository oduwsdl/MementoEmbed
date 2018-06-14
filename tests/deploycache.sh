#!/bin/bash

# Thanks: https://stackoverflow.com/questions/59895/getting-the-source-directory-of-a-bash-script-from-within
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cp testingcache.tar.bz2 /tmp/mementoembed/

cd /tmp/mementoembed/
tar xvfj testingcache.tar.bz2