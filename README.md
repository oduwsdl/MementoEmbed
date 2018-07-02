[![Build Status](https://travis-ci.org/oduwsdl/MementoEmbed.svg?branch=master)](https://travis-ci.org/oduwsdl/MementoEmbed)

# MementoEmbed

A tool to create archive-aware [oEmbed](https://oembed.com/)-compatible embeddable surrogates for archived web pages (mementos). The system currently creates social cards for mementos but will be expanded to include other surrogates like thumbnails. MementoEmbed is different from other surrogate-generation systems in that it provides access to archive-specific information, such as the original domain of the URI-M, its memento-datetime, and to which collection a memento belongs.

**⚠️ NOTE: This tool is still in its early prototyping stage!**

## Run Using Docker

Download the code and build an image as follwoing:

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
