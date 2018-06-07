# MementoEmbed

A tool to create [oEmbed](https://oembed.com/)-compatible embeddable cards for mementoes to summarize archival collections.

## Run Using Docker

Download the coad and build an image as follwoing:

```
$ git clone https://github.com/oduwsdl/MementoEmbed.git
$ cd MementoEmbed
$ docker image build -t membed .
```

Then run a container from this image:

```
$ docker run -it --rm -5550:5550 membed
```

Flags `-it` and `--rm` will make the container connect to the host TTY in interactive mode and remove the container once the process is killed or terminated.
To run the container in detached mode, run the following command instead:

```
$ docker run -d -5550:5550 membed
```

In either case, the application should be accessible at http://localhost:5550/.
