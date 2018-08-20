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

## Run unit tests

The unit tests are designed to be easily run from the setup.py file.

```
$ pip install .
$ python ./setup.py test
```

# Contributing

Please consult the Contribution Guidelines in [CONTRIBUTING.md](https://github.com/oduwsdl/MementoEmbed/blob/master/CONTRIBUTING.md) for submitting bug reports, pull requests, etc.
