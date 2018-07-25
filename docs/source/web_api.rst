=======
Web API
=======

MementoEmbed's Web API consists of several endpoints that produce different types of output. In the following documentation, the symbol ``<URI-M>`` should be replaced with the URI of the memento for which you wish to generate a surrogate.

The two main branches of the MementoEmbed web API are:

* ``/services/memento`` - for getting specific information about a URI-M
* ``/services/product`` - for directly producing a surrogate

Failures
--------

With the exception of the endpoint ``/services/product/thumbnail/<URIM-M>``, all report failure with a MIME-type of ``application/json``.::

    {
    "content": "<div class=\"row\">\n    <div class=\"col\">\n        <p style=\"text-align: left;\">The URL you supplied ( <a href=\"https://example.com)\">https://example.com</a> ) is not a memento or comes from an archive that is not Memento-Compliant.</p>\n        <p style=\"text-align: left;\">\n            For a live web resource, you can create a memento that resides on the web in the following ways:\n            <ul>\n                <li style=\"text-align: left;\">Using the <a href=\"https://web.archive.org\">Internet Archive's Save Page Now button.</a></li>\n                <!-- <li style=\"text-align: left;\">Saving the web page at Archive.is</li> -->\n                <li style=\"text-align: left;\">Using the <a href=\"https://github.com/oduwsdl/archivenow\">ArchiveNow</a> utility.</li>\n                <li style=\"text-align: left;\">Using a browser plugin, like <a href=\"https://chrome.google.com/webstore/detail/mink-integrate-live-archi/jemoalkmipibchioofomhkgimhofbbem?hl=en-US\">Mink</a>.</li>\n            </ul>\n\n        </p>\n        <p style=\"text-align: center; font-weight: bold;\">Happy Memento Making! \ud83d\ude00</p>\n    </div>\n</div>\n",
    "error details": "'Traceback (most recent call last):\\n  File \"/usr/local/lib/python3.6/site-packages/mementoembed/mementoresource.py\", line 80, in get_memento_datetime_from_response\\n    response.headers[\\'memento-datetime\\'],\\n  File \"/usr/local/lib/python3.6/site-packages/requests/structures.py\", line 54, in __getitem__\\n    return self._store[key.lower()][1]\\nKeyError: \\'memento-datetime\\'\\n\\nDuring handling of the above exception, another exception occurred:\\n\\nTraceback (most recent call last):\\n  File \"/usr/local/lib/python3.6/site-packages/mementoembed/services/errors.py\", line 26, in handle_errors\\n    return function_name(urim)\\n  File \"/usr/local/lib/python3.6/site-packages/mementoembed/services/memento.py\", line 35, in contentdata\\n    memento = memento_resource_factory(urim, httpcache)\\n  File \"/usr/local/lib/python3.6/site-packages/mementoembed/mementoresource.py\", line 222, in memento_resource_factory\\n    memento_dt = get_memento_datetime_from_response(response)\\n  File \"/usr/local/lib/python3.6/site-packages/mementoembed/mementoresource.py\", line 85, in get_memento_datetime_from_response\\n    response=response, original_exception=e)\\nmementoembed.mementoresource.NotAMementoError: no memento-datetime header\\n'"
    }

The response consists of two JSON keys:

* ``content`` - HTML containing a formatted error message for inclusion in a web page
* ``error details`` - this provides a Traceback of the MementoEmbed application that may be useful for diagnosing the error if it is a failure in the application

The services produce different HTTP status codes depending on the nature of the response:

* ``200`` - all was successful
* ``404`` - the requested URI-M is not a memento and cannot be serviced by MementoEmbed
* ``504`` - while requesting the URI-M for processing, the connection timed out
* ``400`` - the URI-M submitted is invalid, either lacking a scheme (e.g., http or https) or otherwise not formed according to standards
* ``502`` - while requesting the URI-M for processing, there was a connection error
* ``500`` - the remaining errors are covered by this HTTP status code

Memento Endpoints for Requesting Specific Memento Information
-------------------------------------------------------------

Memento Content
~~~~~~~~~~~~~~~

Endpoint: ``/services/memento/contentdata/<URI-M>``

On success, this service produces an HTTP 200 response with a MIME-type of ``application/json`` that contains information about the content of the memento and its headers::

    {
    "urim": "https://www.webarchive.org.uk/wayback/archive/20090522221251/http://blasttheory.co.uk/",
    "generation-time": "2018-07-20T16:27:10Z",
    "title": "Blast Theory",
    "snippet": "Sam Pearson and Clara Garcia Fraile are in residence for one month Sam Pearson and Clara Garcia Fraile are in residence for one month working on a new project called In My Shoes. They are developin",
    "memento-datetime": "2009-05-22T22:12:51Z"
    }

Best image
~~~~~~~~~~

Endpoint: ``/services/memento/bestimage/<URI-M>``

On success, this service produces an HTTP response with a MIME-type of ``application-json`` that contains information about the image selected by the image selection algorithm::

    {
        "urim": "https://www.webarchive.org.uk/wayback/archive/20090522221251/http://blasttheory.co.uk/",
        "best-image-uri": "https://www.webarchive.org.uk/wayback/archive/20090522221251/http:/blasttheory.co.uk/bt/i/yougetme/ygm_icon.jpg",
        "generation-time": "2018-07-20T16:34:12Z"
    }

Archive data
~~~~~~~~~~~~

Endpoint: ``/services/memento/archivedata/<URI-M>``

On success, this service produces an HTTP response with a MIME-type of ``application-json`` that contains information about the archive, and if possible, archive collection containing the memento::

    {
        "urim": "https://www.webarchive.org.uk/wayback/archive/20090522221251/http://blasttheory.co.uk/",
        "generation-time": "2018-07-20T16:35:34Z",
        "archive-uri": "https://www.webarchive.org.uk",
        "archive-name": "WEBARCHIVE.ORG.UK",
        "archive-favicon": "https://www.webarchive.org.uk/ukwa/static/images/ukwa-icon-16.png",
        "archive-collection-id": null,
        "archive-collection-name": null,
        "archive-collection-uri": null
    }

If the archive collection information is not available, those values are filled with ``null``.

Original Resource data
~~~~~~~~~~~~~~~~~~~~~~

Endpoint: ``/services/memento/originalresourcedata/<URI-M>``

On success, this service produces an HTTP response with a MIME-type of ``application-json`` that contains information about the original resource::

    {
        "urim": "https://www.webarchive.org.uk/wayback/archive/20090522221251/http://blasttheory.co.uk/",
        "generation-time": "2018-07-20T16:36:48Z",
        "original-uri": "http://blasttheory.co.uk/",
        "original-domain": "blasttheory.co.uk",
        "original-favicon": "https://www.blasttheory.co.uk/wp-content/themes/blasttheory/images/bt_icon.ico",
        "original-linkstatus": "Live"
    }


Product Endpoints for Requesting a Surrogate Directly
-----------------------------------------------------

Social Cards
~~~~~~~~~~~~

Endpoint: ``/services/product/socialcard/<URI-M>``

On success, the social card service produces an HTTP 200 status response containing a social card with a MIME-type of ``text/html``. This HTML is suitable for inclusion into a web page::

    <blockquote
        class="mementoembed"
        data-urim="https://www.webarchive.org.uk/wayback/archive/20090522221251/http://blasttheory.co.uk/"
        data-urir="http://blasttheory.co.uk/" data-surrogate-creation-time="2018-07-20T16:08:40Z" data-image="https://www.webarchive.org.uk/wayback/archive/20090522221251/http:/blasttheory.co.uk/bt/i/yougetme/ygm_icon.jpg" data-archive-name="WEBARCHIVE.ORG.UK" data-archive-favicon="https://www.webarchive.org.uk/ukwa/static/images/ukwa-icon-16.png" data-archive-uri="https://www.webarchive.org.uk" data-archive-collection-id="None" data-archive-collection-uri="None" data-archive-collection-name="None" data-original-favicon="https://www.blasttheory.co.uk/wp-content/themes/blasttheory/images/bt_icon.ico" data-original-domain="blasttheory.co.uk" data-original-link-status="Live" data-date="2009-05-22 22:12:51 GMT" style="width: 500px; font-size: 12px; border: 1px solid rgb(231, 231, 231);">
        <div class="me-textright">
            <p class="me-title"><a class="me-title-link" href="https://www.webarchive.org.uk/wayback/archive/20090522221251/http://blasttheory.co.uk/">Blast Theory</a>
            </p>
            <p class="me-snippet">Sam Pearson and Clara Garcia Fraile are in residence for one month Sam Pearson and Clara Garcia Fraile are in residence for one month working on a new project called In My Shoes. They are developin
            </p>
            </div>
    </blockquote>
    <script async src="http://mementoembed.ws-dl.cs.odu.edu/static/js/mementoembed.js" charset="utf-8"></script>


One could conceivably use the output of this endpoint as an argument to the ``src`` attribute in an HTML ``<iframe>`` tag, but we do not recommend this. The HTML is intended to be downloaded and included separately.

On failure, the thumbnail service produces a response with a MIME-type of ``application/json`` that includes the nature of the failure::

    {

    "content": "<div class=\"row\">\n    <div class=\"col\">\n        <p style=\"text-align: left;\">The URL you supplied ( <a href=\"http://example.com)\">http://example.com</a> ) is not a memento or comes from an archive that is not Memento-Compliant.</p>\n        <p style=\"text-align: left;\">\n            For a live web resource, you can create a memento that resides on the web in the following ways:\n            <ul>\n                <li style=\"text-align: left;\">Using the <a href=\"https://web.archive.org\">Internet Archive's Save Page Now button.</a></li>\n                <!-- <li style=\"text-align: left;\">Saving the web page at Archive.is</li> -->\n                <li style=\"text-align: left;\">Using the <a href=\"https://github.com/oduwsdl/archivenow\">ArchiveNow</a> utility.</li>\n                <li style=\"text-align: left;\">Using a browser plugin, like <a href=\"https://chrome.google.com/webstore/detail/mink-integrate-live-archi/jemoalkmipibchioofomhkgimhofbbem?hl=en-US\">Mink</a>.</li>\n            </ul>\n\n        </p>\n        <p style=\"text-align: center; font-weight: bold;\">Happy Memento Making! \ud83d\ude00</p>\n    </div>\n</div>\n",
    "error details": "'Traceback (most recent call last):\\n  File \"/usr/local/lib/python3.6/site-packages/mementoembed/mementoresource.py\", line 80, in get_memento_datetime_from_response\\n    response.headers[\\'memento-datetime\\'],\\n  File \"/usr/local/lib/python3.6/site-packages/requests/structures.py\", line 54, in __getitem__\\n    return self._store[key.lower()][1]\\nKeyError: \\'memento-datetime\\'\\n\\nDuring handling of the above exception, another exception occurred:\\n\\nTraceback (most recent call last):\\n  File \"/usr/local/lib/python3.6/site-packages/mementoembed/services/errors.py\", line 26, in handle_errors\\n    return function_name(urim)\\n  File \"/usr/local/lib/python3.6/site-packages/mementoembed/services/product.py\", line 57, in generate_socialcard_response\\n    httpcache\\n  File \"/usr/local/lib/python3.6/site-packages/mementoembed/mementosurrogate.py\", line 26, in __init__\\n    self.memento = memento_resource_factory(self.urim, self.httpcache)\\n  File \"/usr/local/lib/python3.6/site-packages/mementoembed/mementoresource.py\", line 222, in memento_resource_factory\\n    memento_dt = get_memento_datetime_from_response(response)\\n  File \"/usr/local/lib/python3.6/site-packages/mementoembed/mementoresource.py\", line 85, in get_memento_datetime_from_response\\n    response=response, original_exception=e)\\nmementoembed.mementoresource.NotAMementoError: no memento-datetime header\\n'"
    }

Thumbnails
~~~~~~~~~~

Endpoint: ``/services/product/thumbnail/<URI-M>``

On success, the thumbnail service produces an HTTP 200 status response containing a thumbnail with a MIME-type of ``image/png``.

.. image:: images/thumbnail-example.png

On failure, the thumbnail service produces an HTTP 500 status response with a MIME-type of `application/json` that indicates the nature of the failure::

    {
        "error": "a thumbnail failed to generated in 30 seconds",
        "error details": "'Traceback (most recent call last):\\n  File \"/usr/local/lib/python3.6/site-packages/mementoembed/services/product.py\", line 109, in thumbnail_endpoint\\n    p.wait(timeout=timeout)\\n  File \"/usr/local/lib/python3.6/subprocess.py\", line 1449, in wait\\n    raise TimeoutExpired(self.args, timeout)\\nsubprocess.TimeoutExpired: Command \\'[\\'node\\', \\'mementoembed/static/js/create_screenshot.js\\']\\' timed out after 30 seconds\\n'"
    }

This response contains two keys:

* ``error`` - this provides an explanation of the failure
* ``error details`` - this provides a Traceback of the MementoEmbed application that may be useful for diagnosing the error if it is a failure in the application

**Specifying desired options for the thumbnail with HTTP Prefer**

Using the HTTP ``Prefer`` header specified in `RFC 7240 <https://tools.ietf.org/html/rfc7240>`_, a client can request a thumbnail with specific features. For example, this client has contacted MementoEmbed at endpoint ``/services/product/thumbnail/``, requesting a thumbnail of URI-M ``http://web.archive.org/web/20180128152127/http://www.cs.odu.edu/~mkelly/`` with a viewport width of 4096 pixels and a thumbnail width of 2048 pixels::

    GET /services/product/thumbnail/http://web.archive.org/web/20180128152127/http://www.cs.odu.edu/~mkelly/ HTTP/1.1
    Host: mementoembed.ws-dl.cs.odu.edu
    User-Agent: curl/7.54.0
    Accept: */*
    Prefer: viewport_width=4096,thumbnail_width=2048

The response from MementoEmbed uses the ``Preference-Applied`` header to indicate which preferences have been applied, as shown in the following headers::

    HTTP/1.0 200 OK
    Content-Type: image/png
    Content-Length: 437589
    Preference-Applied: viewport_width=4096,viewport_height=768,thumbnail_width=2048,thumbnail_height=156,timeout=60
    Server: Werkzeug/0.14.1 Python/3.6.5
    Date: Wed, 25 Jul 2018 20:59:21 GMT

    ...437589 bytes of data follows...

MementoEmbed supports several options for specifying desired options for thumbnails.

The following options are supported:

* ``viewport_width`` - the width of the viewport of the browser capturing the snapshot
* ``viewport_height`` - the height of the viewport of the browser capturing the snapshot
* ``thumbnail_width`` - the width of the thumbnail in pixels, the thumbnail will be reduced in size to meet this requirement
* ``thumbnail_height`` - the height of the thumbnail in pixels, the thumbnail will be reduced in size to meet this requirement
* ``timeout`` - how long MementoEmbed should wait for the thumbnail to finish generating before issuing an error
