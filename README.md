[![Build Status](https://travis-ci.org/oduwsdl/MementoEmbed.svg?branch=master)](https://travis-ci.org/oduwsdl/MementoEmbed)
[![Doc Status](https://readthedocs.org/projects/mementoembed/badge/?version=latest&style=flat)](https://mementoembed.readthedocs.io/en/latest/)

# MementoEmbed

![Image of a Social Card](docs/source/images/socialcard-example.png?raw=true "Social Card Example for http://arquivo.pt/wayback/19980205082901/http://www.caleida.pt/saramago/")

A tool to create archive-aware [oEmbed](https://oembed.com/)-compatible embeddable surrogates for archived web pages (mementos). The system currently creates social cards like the one shown above and thumbnails like the one shown below. MementoEmbed is different from other surrogate-generation systems in that it provides access to archive-specific information, such as the original domain of the URI-M, its memento-datetime, and to which collection a memento belongs.

![Image of a Social Card](docs/source/images/thumbnail-example.png?raw=true "Thumbnail Example for http://arquivo.pt/wayback/19980205082901/http://www.caleida.pt/saramago/")

For more information on this application, please visit our [Documentation Page](https://mementoembed.readthedocs.io/en/latest/).

## Installation and Execution

### Installing and Running the Latest Build Using Docker

Because of its complex cross-language and environment dependencies, MementoEmbed is installed via Docker. To run the latest build use the following commands.

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

### Installing and Running Locally

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
* /bin/ - scripts using MementoEmbed libraries (was used for early development, to be removed at some future point)
* /config/ - default Flask configuration for MementoEmbed
* /docs/ - source for documentation of MementoEmbed, products can be viewed at the project [Documentation Page](https://mementoembed.readthedocs.io/en/latest/).
* /githooks/ - hooks for use with Git in development (was an experiment, not currently used)
* /instance/ - default Flask configuration for MementoEmbed
* /mementoembed/ - main MementoEmbed application
* /mementoembed/services/ - code containing source code for the machine-accessible MementoEmbed endpoints
* /mementoembed/static/ - JavaScript and CSS used for the MementoEmbed application
* /mementoembed/templates/ - Jinja2 templates for the MementoEmbed application
* /mementoembed/ui/ - code for the user interface MementoEmbed endpoints
* /tests/ - automated unit tests for core MementoEmbed functionality
* .dockerignore - used to indicate which files Docker should ignore when building an image
* .gitignore - used to indicate which files Git should not commit during development
* .travis.yml - configuration for executing unit tests and testing build of MementoEmbed
* CONTRIBUTING.md - instructions for contributing to this project
* Dockerfile - used to build the docker image
* LICENSE - the license for this project
* MANIFEST.in - used to ensure additional files are installed on the system when pip is run
* README.md - this file
* dockerstart.sh - the script run by Docker to start MementoEmbed once a container is started
* package-lock.json - pakcage version information used by npm
* raiseversion.sh - a script run to raise the version of MementoEmbed in both documentation and source code
* release.sh - script planned for use when releasing MementoEmbed (not currently used, may be removed at some point)
* sample_appconfig.cfg - MementoEmbed configuration used by the Docker container
* setup.py - standard Python installation configuration file

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

Note that integration tests are heavily dependent on environmental factors.

# Contributing

Please consult the Contribution Guidelines in [CONTRIBUTING.md](https://github.com/oduwsdl/MementoEmbed/blob/master/CONTRIBUTING.md) for submitting bug reports, pull requests, etc.
