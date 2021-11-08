#!/bin/bash

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

function test_command(){
    command=$1

    printf "checking for $command [    ]"

    set +e
    which $command > /dev/null
    status=$?

    if [ $status -ne 0 ]; then
        printf "\b\b\b\b\b"
        printf "FAIL]\n"
        echo "$command is required to create an installer"
        exit 2
    fi

    printf "\b\b\b\b\b"
    printf " OK ]\n"

    set -e
}

function test_python_version(){
    desired_version=$1
    PYTHON_VERSION=`python --version | sed 's/Python //g' | awk -F. '{ print $1 }'`

    printf "checking for Python version ${desired_version} [    ]"

    if [ $PYTHON_VERSION -ne ${desired_version} ]; then
        printf "\b\b\b\b\b"
        printf "FAIL]\n"
        echo "Python version $PYTHON_VERSION is not supported, 3 is required."
        exit 2
    fi

    printf "\b\b\b\b\b"
    printf " OK ]\n"

}

function run_command() {
    text_to_print=$1
    command_to_run=$2
    newline=$3

    # echo "executing: ${command_to_run}"

    if [ -z $newline ]; then
        newline="yes"
    fi

    printf "${text_to_print} [    ]"

    command_output_file=`mktemp`

    set +e

    eval "$command_to_run" > $command_output_file 2>&1
    status=$?

    printf "\b\b\b\b\b\b"
    if [ $status -ne 0 ]; then

        printf "[FAIL]\n"
        echo
        cat "$command_output_file"
        echo
        echo "${text_to_print} FAILED"
        exit 2
    fi

    if [ $newline == "nonewline" ]; then
        printf "[ OK ]"
    else
        printf "[ OK ]\n"
    fi

    set -e
}

echo "STARTING: MementoEmbed Linux installer build"

test_command "rm"
test_command "tar"
test_command "sed"
test_command "grep"
test_command "mktemp"
test_command "makeself"
test_command "python"
test_python_version "3"

run_command "acquiring MementoEmbed version" "(grep '__appversion__ = ' ${SCRIPT_DIR}/mementoembed/version.py) | sed 's/.*__appversion__ = //g'" "nonewline"
mementoembed_version=`cat ${command_output_file} | sed "s/'//g"`
echo " --- MementoEmbed version is ${mementoembed_version}"
run_command "cleaning MementoEmbed library build environment" "(cd ${SCRIPT_DIR} && python ./setup.py clean 2>&1)"
run_command "cleaning MementoEmbed library build environment" "(cd ${SCRIPT_DIR} && rm -rf build dist 2>&1)"
run_command "cleaning installer directory" "rm -rf ${SCRIPT_DIR}/installer"
run_command "building MementoEmbed library install" "(cd ${SCRIPT_DIR} && python ./setup.py sdist 2>&1)"
run_command "verifying MementoEmbed library tarball" "ls ${SCRIPT_DIR}/dist/mementoembed-${mementoembed_version}.tar.gz" "nonewline"
echo " --- ${SCRIPT_DIR}/dist/mementoembed-${mementoembed_version}.tar.gz exists"
run_command "copying install script to archive directory" "cp ${SCRIPT_DIR}/mementoembed-install-script.sh ${SCRIPT_DIR}/dist"
#run_command "copying requirements.txt to archive directory" "cp ${SCRIPT_DIR}/requirements.txt ${SCRIPT_DIR}/dist"
run_command "copying package-lock.json to archive directory" "cp ${SCRIPT_DIR}/package-lock.json ${SCRIPT_DIR}/dist"
run_command "copying sample configuration to archive directory" "cp ${SCRIPT_DIR}/sample_appconfig.cfg ${SCRIPT_DIR}/dist"
run_command "copying template configurations to archie directory" "cp ${SCRIPT_DIR}/template_appconfig.cfg ${SCRIPT_DIR}/dist"
run_command "setting install script permissions" "chmod 0755 ${SCRIPT_DIR}/mementoembed-install-script.sh"
run_command "creating directory for installer" "mkdir ${SCRIPT_DIR}/installer"

run_command "executing makeself" "makeself ${SCRIPT_DIR}/dist/ ${SCRIPT_DIR}/installer/install-mementoembed.sh 'MementoEmbed from the Dark and Stormy Archives Project' ./mementoembed-install-script.sh"
installer_file=`cat ${command_output_file} | grep "successfully created" | sed 's/Self-extractable archive "//g' | sed 's/" successfully created.//g'`
echo "DONE: installer available at in ${installer_file}"
