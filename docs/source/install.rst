============
Installation
============

MementoEmbed is written in Python, but we have created several different ways to install it on Linux/Unix. MementoEmbed relies on Redis for caching. Install Redis first and then follow the directions for your applicable Linux/Unix system below.

Installing on a CentOS 8 System
-------------------------------

If you would like to use the RPM installer for RHEL 8 and CentOS 8 systems:

1. download the RPM and save it to the Linux server (e.g., ``MementoEmbed-0.20211106041644-1.el8.x86_64.rpm``)
2. type ``dnf install MementoEmbed-0.20211106041644-1.el8.x86_64.rpm``
3. type ``systemctl start mementoembed.service``

If the service does not work at first, you may need to run `systemctl start redis`.

To remove MementoEmbed, type ``dnf remove MementoEmbed`` (it is case sensitive). The uninstall process will create a tarball of the ``/opt/mementoembed/var`` directory. This contains the thumbnail cache, imagereel cache, and logs. It is left in case the system administrator needs this data.

MementoEmbed can now be accessed from http://localhost:5550/.

Installing on an Ubuntu 21.04+ System
-------------------------------------

If you would like to use the deb installer for RHEL 8 and CentOS 8 systems:

1. download the DEB and save it to the Linux server (e.g., ``MementoEmbed-0.20211112212747.deb``)
2. type ``apt-get update`` ⬅️ this may not be necessary, but is needed in some cases to make sure dependencies are loaded
3. type ``apt-get install ./MementoEmbed-0.20211112212747.deb`` ⬅️ the ``./`` is important, do not leave it off
4. type ``systemctl start mementoembed.service``

If the service does not work at first, you may need to run ``systemctl start redis``.

To remove MementoEmbed, type ``apt-get remove mementoembed`` (it is case sensitive). The uninstall process will create a tarball of the ``/opt/mementoembed/var`` directory. This contains the thumbnail cache, imagereel cache, and logs. It is left in case the system administrator needs this data.

Headless Chromium has a problem on Ubuntu. [The issue](https://bugs.chromium.org/p/chromium/issues/detail?id=1221905&q=Passthrough%20is%20not%20supported%2C%20GL%20is%20swiftshader&can=1) is known to Google. This may manifest in a log with a message such as ``ERROR:gpu_init.cc(441) Passthrough is not supported, GL is disabled``.  MementoEmbed still appears to generate thumbnails, so we are waiting for Google to address the issue.

MementoEmbed can now be accessed from http://localhost:5550/.

Installing on a generic Unix System
-----------------------------------

If you would like to use the generic installer for Unix (including macOS):

1. download the generic installer (e.g., ``install-mementoembed-0.20211112212747.sh``)
2. type ``sudo ./install-mementoembed-0.20211112212747.sh``
3. start MementoEmbed using either ``systemctl start mementoembed.service`` (if your Unix/Linux supports systemd) or ``/opt/mementoembed/start-mementoembed.sh`` if not

MementoEmbed can now be accessed from http://localhost:5550/.

Installing and Running the Latest Docker Build
----------------------------------------------

To run the latest Docker build use the following commands.::

    $ docker pull oduwsdl/mementoembed
    $ docker run -d -p 5550:5550 oduwsdl/mementoembed


MementoEmbed can now be accessed from http://localhost:5550/.

Installing and Running From Source Using Docker
-----------------------------------------------

Download the code and build an image as following:::

    $ git clone https://github.com/oduwsdl/MementoEmbed.git
    $ cd MementoEmbed
    $ docker build -t mementoembed .

Then run a container from this image:::

    $ docker run -it --rm -p 5550:5550 mementoembed

Flags `-it` and `--rm` will make the container connect to the host TTY in interactive mode and remove the container once the process is killed or terminated.
To run the container in detached mode, run the following command instead:::

    $ docker run -d -p 5550:5550 mementoembed


In either case, the application should be accessible at http://localhost:5550/.

Installing and Running Locally From Source With PIP
---------------------------------------------------

Download the code and install it within your Python environment.::

    $ git clone https://github.com/oduwsdl/MementoEmbed.git
    $ cd MementoEmbed
    $ pip install .

Then set it up to run locally using Flask.::

    $ export FLASK_APP=mementoembed
    $ flask run
