[![Build Status](https://travis-ci.org/oduwsdl/MementoEmbed.svg?branch=master)](https://travis-ci.org/oduwsdl/MementoEmbed)
[![Doc Status](https://readthedocs.org/projects/mementoembed/badge/?version=latest&style=flat)](https://mementoembed.readthedocs.io/en/latest/)

# MementoEmbed

![Image of a Social Card](docs/source/images/socialcard-example.png?raw=true "Social Card Example for http://arquivo.pt/wayback/19980205082901/http://www.caleida.pt/saramago/")

MementoEmbed is a tool to create archive-aware embeddable **surrogates** for archived web pages (mementos), like the **social card** above. MementoEmbed is different from other surrogate-generation systems in that it provides access to archive-specific information, such as the original domain of the URI-M, its memento-datetime, and to which collection a memento belongs.

MementoEmbed can also create **browser thumbnails** like the one below.

![Image of a Browser Thumbnail](docs/source/images/thumbnail-example.png?raw=true "Thumbnail Example for http://arquivo.pt/wayback/19980205082901/http://www.caleida.pt/saramago/")

In addition, MementoEmbed can create **imagereels**, animated GIFs of the best five images from the memento, as seen below.

![Image of an Imagereel](docs/source/images/imagereel-example.gif?raw=true "Imagereel example for https://wayback.archive-it.org/2358/20110211072257/http://news.blogs.cnn.com/category/world/egypt-world-latest-news/")

For more information on this application, please visit our [Documentation Page](https://mementoembed.readthedocs.io/en/latest/) and read the [original blog post describing the reasons behind MementoEmbed](https://ws-dl.blogspot.com/2018/08/2018-08-01-preview-of-mementoembed.html).

## Installation and Execution

MementoEmbed relies on Redis for caching. Install Redis first and then follow the directions for your applicable Linux/Unix system below.

### Installing on a CentOS 8 System

If you would like to use the RPM installer for RHEL 8 and CentOS 8 systems:

1. download the RPM and save it to the Linux server (e.g., `MementoEmbed-0.20211106041644-1.el8.x86_64.rpm`)
2. type `dnf install MementoEmbed-0.20211106041644-1.el8.x86_64.rpm`
3. type `systemctl start mementoembed.service`

If the service does not work at first, you may need to run `systemctl start redis`.

To remove MementoEmbed, type `dnf remove MementoEmbed` (it is case sensitive). The uninstall process will create a tarball of the `/opt/mementoembed/var` directory. This contains the thumbnail cache, imagereel cache, and logs. It is left in case the system administrator needs this data.

MementoEmbed can now be accessed from http://localhost:5550/.

### Installing on an Ubuntu 21.04+ System

If you would like to use the deb installer for RHEL 8 and CentOS 8 systems:

1. download the DEB and save it to the Linux server (e.g., `MementoEmbed-0.20211112212747.deb`)
2. type `apt-get update` <-- this may not be necessary, but is needed in some cases to make sure dependencies are loaded
3. type `apt-get install ./MementoEmbed-0.20211112212747.deb` <-- the ./ is important, do not leave it off
4. type `systemctl start mementoembed.service`

If the service does not work at first, you may need to run `systemctl start redis`.

To remove MementoEmbed, type `apt-get remove mementoembed` (it is case sensitive). The uninstall process will create a tarball of the `/opt/mementoembed/var` directory. This contains the thumbnail cache, imagereel cache, and logs. It is left in case the system administrator needs this data.

Headless Chromium has a problem on Ubuntu. [The issue](https://bugs.chromium.org/p/chromium/issues/detail?id=1221905&q=Passthrough%20is%20not%20supported%2C%20GL%20is%20swiftshader&can=1) is known to Google. This may manifest in a log with a message such as `ERROR:gpu_init.cc(441) Passthrough is not supported, GL is disabled`.  MementoEmbed still appears to generate thumbnails, so we are waiting for Google to address the issue.

MementoEmbed can now be accessed from http://localhost:5550/.

### Installing on a generic Unix System

If you would like to use the generic installer for Unix (including macOS):

1. download the generic installer (e.g., `install-mementoembed-0.20211112212747.sh`)
2. type `sudo ./install-mementoembed-0.20211112212747.sh`
3. start MementoEmbed using either `systemctl start mementoembed.service` (if your Unix/Linux supports systemd) or `/opt/mementoembed/start-mementoembed.sh` if not

MementoEmbed can now be accessed from http://localhost:5550/.

### Installing and Running the Latest Docker Build

To run the latest Docker build use the following commands.

```
$ docker pull oduwsdl/mementoembed
$ docker run -d -p 5550:5550 oduwsdl/mementoembed
```

MementoEmbed can now be accessed from http://localhost:5550/.

### Installing and Running From Source Using Docker

Download the code and build an image as following:

```
$ git clone https://github.com/oduwsdl/MementoEmbed.git
$ cd MementoEmbed
$ docker build -t mementoembed .
```

Then run a container from this image:

```
$ docker run -it --rm -p 5550:5550 mementoembed
```

Flags `-it` and `--rm` will make the container connect to the host TTY in interactive mode and remove the container once the process is killed or terminated.
To run the container in detached mode, run the following command instead:

```
$ docker run -d -p 5550:5550 mementoembed
```

In either case, the application should be accessible at http://localhost:5550/.

### Installing and Running Locally From Source With PIP

Download the code and install it within your Python environment.

```
$ git clone https://github.com/oduwsdl/MementoEmbed.git
$ cd MementoEmbed
$ pip install .
```

Then set it up to run locally using Flask.

```
$ export FLASK_APP=mementoembed
$ flask run
```

### Loading a Desired Configuration

The configuration options for MementoEmbed are documented in `sample_appconfig.cfg`.

The defaults are stored in `config/default.py`.

To use your own configuration file, copy `sample_appconfig.cfg`, make modifications, and place it in `/etc/mementoembed.cfg`. Then run the application locally as described above.

To use your own configuration file stored at `/path/to/my/config.cfg` with a Docker image, use the `-v` Docker option:
`docker run -it --rm -v /path/to/my/config.cfg:/etc/mementoembed.cfg  -p 5550:5550 oduwsdl/mementoembed`

## Directory Layout

The following directory structure exists for organizing MementoEmbed:
* /config/ - default Flask configuration for MementoEmbed
* /docs/ - source for documentation of MementoEmbed, products can be viewed at the project [Documentation Page](https://mementoembed.readthedocs.io/en/latest/).
* /githooks/ - hooks for use with Git in development (was an experiment, not currently used)
* /mementoembed/ - main MementoEmbed application
* /mementoembed/services/ - code containing source code for the machine-accessible MementoEmbed endpoints
* /mementoembed/static/ - JavaScript and CSS used for the MementoEmbed application
* /mementoembed/templates/ - Jinja2 templates for the MementoEmbed application
* /mementoembed/ui/ - code for the user interface MementoEmbed endpoints
* /tests/unit - automated unit tests for core MementoEmbed functionality
* /tests/integration - automated integration tests to run against a running MementoEmbed container
* .dockerignore - used to indicate which files Docker should ignore when building an image
* .gitignore - used to indicate which files Git should not commit during development
* .travis.yml - configuration for executing unit tests and testing build of MementoEmbed
* CONTRIBUTING.md - instructions for contributing to this project
* Dockerfile - used to build the docker image
* LICENSE - the license for this project
* MANIFEST.in - used to ensure additional files are installed on the system when pip is run
* Makefile - used to build install packages
* README.md - this file
* dockerstart.sh - the script run by Docker to start MementoEmbed once a container is started
* mementoembed-install-script.sh - script included in the generic Unix install package
* mementembed.control - DEB installer information file
* mementoembed.postinst - DEB installer post-install script
* mementoembed.postun - DEB installer post-uninstall script
* mementoembed.presint - DEB installer pre-install script
* mementoembed.spec - RPM installer configuration file
* package-lock.json - pakcage version information used by npm for thumbnail generation
* raiseversion.sh - a script run to raise the version of MementoEmbed in both documentation and source code
* release.sh - script planned for use when releasing MementoEmbed (not currently used, may be removed at some point)
* requirements.txt - listing of requirements used in the Docker container's Python environment
* sample_appconfig.cfg - MementoEmbed configuration used by the Docker container
* setup.py - standard Python installation configuration file
* tagversion.sh - a script run to raise the version of MementoEmbed and tag it for release
* template_appconfig.cfg - a template of a MementoEmbed configuration used by the generic Unix, DEB, and RPM installers

## Run unit tests

The unit tests are designed to be easily run from the setup.py file.

```
$ pip install .
$ python ./setup.py test
```

## Run integration tests

With a fully operational MementoEmbed, integration tests are possible.

```
python -m unittest discover -s tests/integration
```

Integration tests, by default, assume that the instance to be tested is running at port 5550. This can be altered with the `TESTPORT` environment variable, like so: `export TESTPORT=9000`.

Integration tests are heavily dependent on environmental factors such as the current state of web archive playback systems. The favicon detection appears to be especially unpredictable. Because of this, we recommend that integration tests be reviewed by humans and not executed automatically on build.

## Run CentOS 8 test environment

```
$ docker build --rm -t local/c8-systemd -f tests/installer/centos8/centos8-systemd-Dockerfile .
$ docker run --privileged -v /sys/fs/cgroup:/sys/fs/cgroup:ro -d -p 5550:5550 local/c8-systemd
```

From here use common docker commands (e.g., `docker cp`, `docker exec`) to interact with the container.

## Run Ubuntu 21.04 test environment

```
$ docker build --rm -t local/u2104-systemd -f tests/installer/ubuntu2104/ubuntu2104-systemd-Dockerfile .
$ docker run --privileged -v /sys/fs/cgroup:/sys/fs/cgroup:ro -d -p 5550:5550 local/u2104-systemd
```

From here use common docker commands (e.g., `docker cp`, `docker exec`) to interact with the container.

# Contributing

Please consult the Contribution Guidelines in [CONTRIBUTING.md](https://github.com/oduwsdl/MementoEmbed/blob/master/CONTRIBUTING.md) for submitting bug reports, pull requests, etc.
