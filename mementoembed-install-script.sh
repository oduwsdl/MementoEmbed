#!/bin/bash

set -e

function test_command(){
    command=$1

    printf "checking for command: $command [    ]"

    set +e
    which $command > /dev/null
    status=$?

    if [ $status -ne 0 ]; then
        printf "\b\b\b\b\b"
        printf "FAIL]\n"
        echo "the command '$command' is required to install MementoEmbed; it was not detected in your PATH"
        exit 2
    fi

    printf "\b\b\b\b\b"
    printf " OK ]\n"

    set -e
}

function test_access() {
    directory=$1
    printf "verifying that user `whoami` has write access to $directory [    ]"

    set +e
    touch ${directory}/mementoembed-install-testfile.deleteme > /dev/null 2>&1
    status=$?

    printf "\b\b\b\b\b"

    if [ $status -ne 0 ]; then
        
        printf "FAIL]\n"
        echo "this installer needs to be able to write to '${directory}', which `whoami` cannot write to, please run it as a user with these permissions"
        exit 22
    fi

    rm ${directory}/mementoembed-install-testfile.deleteme
    printf " OK ]\n"

    set -e
}

function run_command() {
    text_to_print=$1
    command_to_run=$2
    newline=$3

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

function verify_absolute_path() {
    directory_to_check=$1

    printf "checking if $directory_to_check is an absolute path [    ]"
    printf "\b\b\b\b\b\b"

    if [ "${directory_to_check:0:1}" = "/" ]; then
        printf "[ OK ]\n"
        absolute_path_check=0
    else
        printf "[FAIL]\n"
        absolute_path_check=1
    fi
}

function check_for_systemctl() {
    printf "checking for systemctl -- does this server run systemd? [    ]"

    set +e
    which systemctl
    status=$?
    SYSTEMD_SERVER=$status

    printf "\b\b\b\b\b\b"

    if [ $status -eq 0 ]; then
        printf "[ OK ]\n"
        systemctl_check=0
    else
        printf "[ NO ]\n"
        systemctl_check=1
    fi
    set -e
}

function check_for_systemd() {
    printf "checking for systemd [    ]"

    printf "\b\b\b\b\b\b"

    # not all systemd servers have this directory
    # checkdir="/run/systemd/system"

    # Ubuntu 21.04 and Centos 8 have this directory
    checkdir="/etc/systemd/system"

    if [[ -e ${checkdir} ]]; then
        printf "[ OK ]\n"
        systemd_check=0
    else
        printf "[ NO ]\n"
        systemd_check=1
    fi

}

function check_for_checkconfig() {
    printf "checking for checkconfig -- does this server use initd runlevels instead of systemd? [    ]"

    set +e
    which systemctl > /dev/null
    status=$?
    SYSTEMD_SERVER=$status

    printf "\b\b\b\b\b\b"

    if [ $status -eq 0 ]; then
        printf "[ OK ]\n"
        checkconfig_check=0
    else
        printf "[ NO ]\n"
        checkconfig_check=1
    fi
    set -e
}

function create_generic_startup_scripts() {

    printf "creating startup wrapper [    ]"

    set +e
    cat <<EOF > ${INSTALL_DIRECTORY}/start-mementoembed.sh
#!/bin/bash
set -e

printf "starting MementoEmbed [    ]"

${INSTALL_DIRECTORY}/mementoembed-virtualenv/bin/waitress-serve --host=${FLASK_IP} --port=${FLASK_PORT} --call mementoembed:create_app &
status=\$?
pid=\$!

if [ \$status -eq 0 ]; then
    echo \$pid > ${INSTALL_DIRECTORY}/var/run/mementoembed.pid
    printf "[ OK ]\n"
else
    printf "[FAIL]\n"
fi

EOF
    status=$?

    printf "\b\b\b\b\b\b"

    if [ $status -eq 0 ]; then
        printf "[ OK ]\n"
    else
        printf "[FAIL]\n"
        echo "FAILED: could not create MementoEmbed startup wrapper"
        exit 2
    fi
    set -e

    printf "creating shutdown wrapper [    ]"

    set +e
    cat <<EOF > ${INSTALL_DIRECTORY}/stop-mementoembed.sh
#!/bin/bash
set -e

printf "stopping MementoEmbed "

pid=\`cat ${INSTALL_DIRECTORY}/var/run/mementoembed.pid\`
kill \$pid

ps -ef | grep \$pid | grep -v \$pid
status=$?

if [ $status -eq 0 ]; then
    printf "[ OK ]\n"
    rm ${INSTALL_DIRECTORY}/var/run/mementoembed.pid
else
    printf "[FAIL]\n"
    echo "could not stop process \$pid"
fi
EOF
    status=$?

    printf "\b\b\b\b\b\b"

    if [ $status -eq 0 ]; then
        printf "[ OK ]\n"
    else
        printf "[FAIL]\n"
        echo "FAILED: could not create MementoEmbed startup wrapper"
        exit 2
    fi
    set -e

    run_command "setting permissions on startup wrapper" "chmod 0755 ${INSTALL_DIRECTORY}/start-mementoembed.sh"
    run_command "setting permissions on shutdown wrapper" "chmod 0755 ${INSTALL_DIRECTORY}/stop-mementoembed.sh"
}

function create_systemd_startup() {

    printf "creating systemd MementoEmbed service file [    ]"

    set +e
    cat <<EOF > /etc/systemd/system/mementoembed.service
[Unit]
Description=The MementoEmbed service

[Service]
ExecStart=${INSTALL_DIRECTORY}/mementoembed-virtualenv/bin/waitress-serve --host=${FLASK_IP} --port=${FLASK_PORT} --call mementoembed:create_app
User=${MEMENTOEMBED_USER}

[Install]
WantedBy=multi-user.target
EOF
    status=$?
    set -e

    printf "\b\b\b\b\b\b"
    if [ $status -eq 0 ]; then
        printf "[ OK ]\n"
    else
        printf "[FAIL]\n"
        exit 2
    fi
}

function update_configuration_for_environment_and_install() {

    printf "setting configuration based on install environment: [    ]"

    sed "s?{{ INSTALL_DIRECTORY }}?${INSTALL_DIRECTORY}?g" ${INSTALL_DIRECTORY}/template_appconfig.cfg > /tmp/me.cfg1
    sed "s?{{ LOG_DIRECTORY }}?${INSTALL_DIRECTORY}/var/log?g" /tmp/me.cfg1 > /tmp/me.cfg2
    sed "s?{{ WORKING_DIRECTORY }}?${INSTALL_DIRECTORY}/var/run?g" /tmp/me.cfg2 > /tmp/me.cfg3

    set +e
    grep "{{ [A-Z_]* }}" /tmp/m3.cfg > /dev/null 2>&1
    status=$?
    set -e

    if [ $status -eq 0 ]; then
        printf "\b\b\b\b\b"
        printf "FAIL]\n"
        echo "something went wrong updating the configuration with the appropriate values"
    else
        printf "\b\b\b\b\b"
        printf " OK ]\n"
    fi

    printf "copying configuration file to /etc/mementoembed.cfg [    ]"

    cp /tmp/me.cfg3 /etc/mementoembed.cfg
    status=$?

    if [ $status -ne 0 ]; then
        printf "\b\b\b\b\b"
        printf "FAIL]\n"
        echo "could not copy the updated configuration to the /etc/ directory"
    else
        printf "\b\b\b\b\b"
        printf " OK ]\n"
    fi
}

function perform_install() {

    test_command "ls"
    test_command "mkdir"
    test_command "touch"
    test_command "whoami"
    test_command "tar"
    test_command "dirname"
    test_command "python"
    test_command "virtualenv"
    test_command "node"
    test_command "npm"

    test_access `dirname ${INSTALL_DIRECTORY}`
    test_access "/etc"

    run_command "setting install directory to $INSTALL_DIRECTORY" ""

    verify_absolute_path "$INSTALL_DIRECTORY"
    if [ $absolute_path_check -ne 0 ]; then
        echo "please specify an absolute path for the installation directory"
        exit 22
    fi

    run_command "setting umask to 0022 for duration of install" "umask 0022"

    run_command "creating $INSTALL_DIRECTORY" "mkdir -p $INSTALL_DIRECTORY"
    run_command "creating ${INSTALL_DIRECTORY}/var/run" "mkdir -p $INSTALL_DIRECTORY/var/run"
    run_command "creating ${INSTALL_DIRECTORY}/var/log" "mkdir -p $INSTALL_DIRECTORY/var/log"
    run_command "removing existing virtualenv, if present" "rm -rf $INSTALL_DIRECTORY/mementoembed-virtualenv"

    run_command "discovering MementoEmbed archive" "ls mementoembed-*.tar.gz"
    MEMENTOEMBED_TARBALL=`cat ${command_output_file}`

    run_command "creating virtualenv for MementoEmbed" "virtualenv $INSTALL_DIRECTORY/mementoembed-virtualenv --python ${PYTHON_EXE}"
    run_command "installing MementoEmbed and dependencies" "${INSTALL_DIRECTORY}/mementoembed-virtualenv/bin/pip install --no-cache-dir ${MEMENTOEMBED_TARBALL}"
    run_command "installing waitress" "${INSTALL_DIRECTORY}/mementoembed-virtualenv/bin/pip install waitress"
    run_command "copying package-lock.json" "cp package-lock.json ${INSTALL_DIRECTORY}"
    run_command "installing NodeJS dependencies" "(cd ${INSTALL_DIRECTORY}; npm install --save)"
#    run_command "establishing package.json" "(cd ${INSTALL_DIRECTORY}; npm init)"
    run_command "removing package-lock.json" "rm ${INSTALL_DIRECTORY}/package-lock.json"
    run_command "installing Puppeteer" "(cd ${INSTALL_DIRECTORY}; npm install puppeteer --save --unsafe-perm)"

    run_command "copying template configuration file into ${INSTALL_DIRECTORY}" "cp template_appconfig.cfg ${INSTALL_DIRECTORY}"

    update_configuration_for_environment_and_install

    if [ $FORCE_SYSTEMD -eq 0 ]; then
        create_systemd_startup
    fi

    check_for_systemd
    if [ $systemd_check -ne 0 ]; then
        check_for_checkconfig
        if [ $checkconfig_check -ne 0 ]; then
            create_generic_startup_scripts
            echo
            echo "Notes:"
            echo "* to start MementoEmbed, run ${INSTALL_DIRECTORY}/start-mementoembed.sh"
            echo "* to stop MementoEmbed, run ${INSTALL_DIRECTORY}/stop-mementoembed.sh"

            # TODO: check for macOS and create an icon or something in /Applications for the user to start it there
        else
            create_initd_startup
        fi
    else
        create_systemd_startup
    fi

}

echo
echo "Welcome to MementoEmbed - beginning Unix/Linux install"
echo

INSTALL_DIRECTORY="/opt/mementoembed"
FLASK_PORT=5550
FLASK_IP="0.0.0.0"
MEMENTOEMBED_USER="root"
FORCE_SYSTEMD=1

while test $# -gt 0; do

    case "$1" in
        --install-directory)
        shift
        INSTALL_DIRECTORY=$1
        ;;
        --service-port)
        shift
        FLASK_PORT=$1
        ;;
        --cli-wrapper-path)
        shift
        WRAPPER_SCRIPT_PATH=$1
        ;;
        --mementoembed-user)
        shift
        MEMENTOEMBED_USER=$1
        ;;
        --python-exe)
        shift
        PYTHON_EXE=$1
        ;;
        --force-systemd)
        shift
        FORCE_SYSTEMD=0
        ;;
        --force-initd)
        shift
        FORCE_INITD=0
        ;;
        --django_IP)
        shift
        FLASK_IP=$1
        ;;
    esac
    shift

done

echo "installing to directory ${INSTALL_DIRECTORY}"

perform_install $@

echo
echo "Done with Unix/Linux install. Please read the documentation for details on more setup options and how to use MementoEmbed."
