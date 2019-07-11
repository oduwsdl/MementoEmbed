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

On success, this service produces an HTTP 200 response with a MIME-type of ``application-json`` that contains information about the image selected by the image selection algorithm::

    {
        "urim": "https://www.webarchive.org.uk/wayback/archive/20090522221251/http://blasttheory.co.uk/",
        "best-image-uri": "https://www.webarchive.org.uk/wayback/archive/20090522221251im_/http:/blasttheory.co.uk/bt/i/dotf/Untitled-1.jpg",
        "generation-time": "2019-06-05T19:19:36Z"
    }

Image data
~~~~~~~~~~

Endpoint: ``/services/memento/imagedata/<URI-M>``

This service exposes the information used to rank images for selection with social cards. On success, this service produces an HTTP 200 response with a MIME-type of ``application-json`` that contains information about all images discovered in the memento::

    {
        "urim": "https://www.webarchive.org.uk/wayback/archive/20090522221251/http://blasttheory.co.uk/",
        "processed urim": "https://www.webarchive.org.uk/wayback/archive/20090522221251im_/http://blasttheory.co.uk/",
        "generation-time": "2019-05-30T03:19:08Z",
        "images": {
            "https://www.webarchive.org.uk/wayback/archive/20090522221251im_/http:/blasttheory.co.uk/bt/pe/bt_logo.gif": {
                "content-type": "image/gif",
                "magic type": "GIF image data, version 89a, 169 x 28",
                "imghdr type": "gif",
                "width": 169,
                "height": 28,
                "blank columns in histogram": 14,
                "size in pixels": 4732,
                "ratio width/height": 6.035714285714286,
                "byte size": 2346,
                "N": 14,
                "n": 1,
                "k1": 0.1,
                "k2": 0.4,
                "k3": 10,
                "k4": 0.5,
                "calculated score": 1751.082142857143
            },
            ... other records omitted for brevity ...
        },
        "ranked images": [
            "https://www.webarchive.org.uk/wayback/archive/20090522221251im_/http:/blasttheory.co.uk/bt/i/dotf/Untitled-1.jpg",
            "https://www.webarchive.org.uk/wayback/archive/20090522221251im_/http:/blasttheory.co.uk/bt/i/cysmn/cy_icon.jpg",
            "https://www.webarchive.org.uk/wayback/archive/20090522221251im_/http:/blasttheory.co.uk/bt/i/trucold/trucold_icon.jpg",
            "https://www.webarchive.org.uk/wayback/archive/20090522221251im_/http:/blasttheory.co.uk/bt/i/yougetme/ygm_icon.jpg",
            "https://www.webarchive.org.uk/wayback/archive/20090522221251im_/http:/blasttheory.co.uk/bt/i/ulrikeandeamon/ulrikeandeamon_small.jpg",
            "https://www.webarchive.org.uk/wayback/archive/20090522221251im_/http:/blasttheory.co.uk/bt/i/rider_spoke/rs_icon.jpg",
            "https://www.webarchive.org.uk/wayback/archive/20090522221251im_/http:/blasttheory.co.uk/bt/i/uncleroy/ur_icon.jpg",
            "https://www.webarchive.org.uk/wayback/archive/20090522221251im_/http:/blasttheory.co.uk/bt/pe/bt_logo.gif",
            "https://www.webarchive.org.uk/wayback/archive/20090522221251im_/http:/blasttheory.co.uk/bt/pe/latest.gif",
            "https://www.webarchive.org.uk/wayback/archive/20090522221251im_/http:/blasttheory.co.uk/bt/pe/about.gif",
            "https://www.webarchive.org.uk/wayback/archive/20090522221251im_/http:/blasttheory.co.uk/bt/pe/home.gif",
            "https://www.webarchive.org.uk/wayback/archive/20090522221251im_/http:/blasttheory.co.uk/bt/pe/recent.gif",
            "https://www.webarchive.org.uk/wayback/archive/20090522221251im_/http:/blasttheory.co.uk/bt/pe/types.gif",
            "https://www.webarchive.org.uk/wayback/archive/20090522221251im_/http:/blasttheory.co.uk/bt/pe/chrono.gif"
        ]
    }

Each record in the ``images`` dictionary has a key of the URI-M of the image with the following values:

* ``content-type`` - the value of the ``content-type`` HTTP header
* ``magic type`` - the file magic value of the image
* ``imghdr type`` - the image type as determined by the Python ``imghdr`` library
* ``width`` - the width of the image, in pixels
* ``height`` - the height of the image, in pixels
* ``blank columns in histogram`` - a high number of columns with a value of 0 indicates an image of few colors, likely text used for navigational hints; listed as `h` in the ranking equation below
* ``size in pixels`` - the overall number of pixels in the image determined by ``width`` multiplied by ``height``; `s` in the ranking equation
* ``ratio width/height`` - the ratio of width to height, which can be useful fo detecting advertising banners; `r` in the ranking equation
* ``byte size`` - the size of the image, in bytes, useful for detecting small images typically used for spacing
* ``N`` - the number of images detected on the page
* ``n`` - the order the image was detected on the page
* ``k1`` - the weight used for the first term of the ranking equation (N - n) 
* ``k2`` - the weight used in the ranking equation for the size of the image in pixels
* ``k3`` - the weight used in the ranking equation for the number of blank columns in the histogram
* ``k4`` - the weight used in the ranking equation for the ratio of width/height
* ``calculated score`` - the score, as determined by the ranking equation; `S` in the equation below

The current image ranking equation is as follows:

.. image:: images/image_eq.png

After the ``images`` list is a ``ranked images`` list containing the URI-Ms of each image in order by score.

Archive data
~~~~~~~~~~~~

Endpoint: ``/services/memento/archivedata/<URI-M>``

On success, this service produces an HTTP 200 response with a MIME-type of ``application-json`` that contains information about the archive, and if possible, archive collection containing the memento::

    {
        "urim": "https://www.webarchive.org.uk/wayback/archive/20090522221251/http://blasttheory.co.uk/",
        "generation-time": "2019-06-05T19:18:18Z",
        "archive-uri": "https://www.webarchive.org.uk",
        "archive-name": "WEBARCHIVE.ORG.UK",
        "archive-favicon": "https://www.webarchive.org.uk/favicon.ico",
        "archive-collection-id": null,
        "archive-collection-name": null,
        "archive-collection-uri": null
    }

If the archive collection information is not available, those values are filled with ``null``. Collection information is only currently available for Archive-It and Webrecorder collections.

Original Resource data
~~~~~~~~~~~~~~~~~~~~~~

Endpoint: ``/services/memento/originalresourcedata/<URI-M>``

On success, this service produces an HTTP 200 response with a MIME-type of ``application-json`` that contains information about the original resource::

    {
        "urim": "https://www.webarchive.org.uk/wayback/archive/20090522221251/http://blasttheory.co.uk/",
        "generation-time": "2018-07-20T16:36:48Z",
        "original-uri": "http://blasttheory.co.uk/",
        "original-domain": "blasttheory.co.uk",
        "original-favicon": "https://www.blasttheory.co.uk/wp-content/themes/blasttheory/images/bt_icon.ico",
        "original-linkstatus": "Live"
    }

Seed data
~~~~~~~~~

Endpoint: ``/services/memento/seeddata/<URI-M>``

On success, this service produces an HTTP 200 response with a MIME-type of ``application-json`` that contains information about the seed::

    {
        "urim": "https://www.webarchive.org.uk/wayback/archive/20090522221251/http://blasttheory.co.uk/",
        "generation-time": "2019-05-04T16:16:55Z",
        "timemap": "https://www.webarchive.org.uk/wayback/archive/timemap/link/http://blasttheory.co.uk/",
        "original-url": "http://blasttheory.co.uk/",
        "memento-count": 80,
        "first-memento-datetime": "2009-05-22T22:12:30Z",
        "first-urim": "https://www.webarchive.org.uk/wayback/archive/20090522221230mp_/http://www.blasttheory.co.uk/",
        "last-memento-datetime": "2019-04-01T04:42:08Z",
        "last-urim": "https://www.webarchive.org.uk/wayback/archive/20190401044208mp_/https://www.blasttheory.co.uk/",
        "metadata": {}
    }

The ``originalresourcedata`` endpoint returns information about the original resource. In contrast, the ``seeddata`` service provides information from an archive's perspective, including information about other mementos.  Web archives often contain the first and last URI-M and memento-datetime in the Memento headers, but not all do. This service finds the other mementos available at the archive and creates the first and last entries for you.

For Archive-It mementos, the ``application-json`` contains the metadata supplied by the collection curator for this seed::

    {
        "urim": "https://wayback.archive-it.org/2358/20110213141707/http://twitter.com/DailyNewsEgypt/",
        "generation-time": "2019-05-04T16:16:22Z",
        "timemap": "https://wayback.archive-it.org/2358/timemap/link/http://twitter.com/DailyNewsEgypt/",
        "original-url": "http://twitter.com/DailyNewsEgypt/",
        "memento-count": 223,
        "first-memento-datetime": "2011-02-13T14:17:07Z",
        "first-urim": "https://wayback.archive-it.org/2358/20110213141707/http://twitter.com/DailyNewsEgypt",
        "last-memento-datetime": "2014-12-04T14:01:29Z",
        "last-urim": "https://wayback.archive-it.org/2358/20141204140129/https://twitter.com/DailyNewsEgypt/",
        "metadata": [
            {
                "title": "The Daily News Egypt on Twitter",
                "videos": [
                    "912 Videos Captured"
                ],
                "subject": [
                    "Revolutions--Egypt",
                    "Social media--Political aspects"
                ],
                "language": [
                    "en"
                ],
                "format": [
                    "Web sites"
                ],
                "type": [
                    "Interactive Resource",
                    "Interactive Resource"
                ],
                "relation": [
                    "January 25th Revolution Web sites"
                ],
                "collector": [
                    "American University in Cairo. Rare Books and Special Collections Library",
                    "American University in Cairo. Rare Books and Special Collections Library"
                ]
            }
        ]
    }


Note that the ``metadata`` key is a list. Sometimes an Archive-It collection contains the same seed multiple times. Each instance of the same seed will be a separate list entry in value for the ``metadata`` key.

If data on other mementos at the archive is not available, then a ``seeddata-error`` key will exist, the ``memento-count``, ``first-urim``, ``last-urim``, ``first-memento-datetime``, and ``last-memento-datetime`` values will be set to ``null``::

    {
        "urim": "https://webrecorder.io/despens/bear-with-me/list/bookmarks/b1/20170318154741/http://bearwithme.theater/archive/",
        "generation-time": "2019-07-10T21:17:52Z",
        "timemap": "https://content.webrecorder.io/despens/bear-with-me/list/bookmarks/b1/timemap/link/http://bearwithme.theater/archive/",
        "original-url": "http://bearwithme.theater/archive/",
        "memento-count": null,
        "seeddata-error": "There was an issue processing the TimeMap discovered at https://content.webrecorder.io/despens/bear-with-me/list/bookmarks/b1/timemap/link/http://bearwithme.theater/archive/",
        "first-memento-datetime": null,
        "first-urim": null,
        "last-memento-datetime": null,
        "last-urim": null,
        "metadata": {}
    }

Paragraph ranking
~~~~~~~~~~~~~~~~~

Endpoint: ``/services/memento/paragraphrank/<URI-M>``

On success, this service provides an HTTP 200 response with a MIME-type of ``application-json`` that contains a set of paragraphs discovered in the memento::

    {
        "urim": "https://www.webarchive.org.uk/wayback/archive/20090522221251/http://blasttheory.co.uk/",
        "generation-time": "2019-06-03T21:24:46Z",
        "algorithm": "readability",
        "scored paragraphs": [
            {
                "score": 39.42995104039168,
                "text": "Sam Pearson and Clara Garcia Fraile are in residence for one month Sam Pearson and Clara Garcia Fraile are in residence for one month working on a new project called In My Shoes. They are developing a 'wearable film' which seemingly places the viewer within someone else's body.    This is our first residency at 20 Wellington Road and we are delighted to welcome, support and mentor Sam and Clara on this exciting project.    They have successfully received research and development funding from the Arts Council South East and are supported by Lighthouse.    For more information     www.parachutesandpuzzles.com       Ulrike and Eamon Compliant premieres at 53rd Venice Biennale Blast Theory presents a new work 'Ulrike and Eamon Compliant', commissioned by the De La Warr Pavilion for the 53rd Venice Biennale.    At the Palazzo Zenobio  Fondamenta del Soccorso  Dorodurso  Venice, Italy    Dates: 4th - 7th June, daily 10am - 6pm    Ulrike and Eamon Compliant is a new ambulatory work exploring subjectivity in the heart of the streets, squares and churches of Venice. It invites audiences to become participants and interlocutors with the artists.    Developed with the support of the Mixed Reality Lab, University of Nottingham and made possible by the generous support of Arts Council England and Turning Point South East with the cooperation of Nuova Icona and Oratorio di San Ludovico.    www.dlwp.com       Shockwave developer required We're looking for an experienced Shockwave 3D developer to take responsibility for bug-fixing an existing Shockwave 3D client used for our online performances.     You will be responsible for identifying and implementing a solution, liaising with the original developers and preparing tests for signing off the work.    For full details and how to apply please download the pdf.       Rider Spoke reviewed in RealTime Arts Magazine David Williams took part in Rider Spoke in Sydney. To find out what he thought read his review published in RealTime Arts Magazine here    www.realtimearts.net       Desert Rain acclaimed in The Guardian Lyn Gardner has listed nine productions since 1983 that transformed theatre and has included Desert Rain at the Riverside Studios.    Link: www.guardian.co.uk/stage       New blog on Pervasive Games In the run up to the publication of Pervasive Games: Theory and Design for which Matt Adams has written a text, the authors - Markus Montola and Jaakko Stenros - have started a blog on pervasive games.    pervasivegames.wordpress.com                               News              Archive"
            },
            {
                "score": 31.514459798994977,
                "text": "Online                 Video                 Live                  Games                 Mobile                 Gallery \t\t\t\tResearch \t\t\t\t                       Ulrike and Eamon Compliant                         Ulrike and Eamon Compliant is a new ambulatory work exploring subjectivity. more...                           You Get Me                         You Get Me is a work about understanding, intimacy              and mediation. more...                          Rider Spoke                         Rider Spoke is a work for cyclists. more...                          Day Of The Figurines                                    Day Of The Figurines is set in a fictional              town that is littered, dark and underpinned with steady decay. more...                          Uncle Roy All Around              You                         Using web cams, audio and text messages players              must work together. more...                          Can You See Me Now?                                    Tracked by satellites, Blast Theory's runners              appear online next to your player on a map of the city centre. more...                          TRUCOLD                         Darkness, fog and a slow shutter speed all              accentuate the ambiguity and precariousness of urban experience. more..."
            },
            ... additional entries omitted for brevity ...
        ]
    }

The keys of this JSON response have the following meanings:

* ``urim`` - the URI-M submitted to the service
* ``generation-time`` - the time this response was generated
* ``algorithm`` - the algorithm used to rank the paragraphs

Each list entry in ``scored paragraphs`` contains dictionaries with the following keys:

* ``score`` - the score of the paragraph as determined by the algorithm
* ``text`` - the text of the paragraph with this score

Currently `readability`, from the `ARC90 Readability project <https://github.com/buriy/python-readability>`_, is the only paragraph ranking algorithm available. 


Sentence ranking
~~~~~~~~~~~~~~~~~

Endpoint: ``/services/memento/sentencerank/<URI-M>``

On success, this service provides an HTTP 200 response with a MIME-type of ``application-json`` that contains a set of setences discovered in the memento::

    {
        "urim": "https://www.webarchive.org.uk/wayback/archive/20090522221251/http://blasttheory.co.uk/",
        "generation-time": "2019-06-03T21:34:03Z",
        "paragraph scoring algorithm": "readability",
        "sentence ranking algorithm": "lede3",
        "scored sentences": [
            {
                "paragraph score": 39.42995104039168,
                "sentence score": 15,
                "text": "Sam Pearson and Clara Garcia Fraile are in residence for one month Sam Pearson and Clara Garcia Fraile are in residence for one month working on a new project called In My Shoes."
            },
            {
                "paragraph score": 39.42995104039168,
                "sentence score": 14,
                "text": "They are developing a 'wearable film' which seemingly places the viewer within someone else's body."
            },
        ... other sentences omitted for brevity ...
        ]
    }

The keys of this JSON response have the following meanings:

* ``urim`` - the URI-M submitted to the service
* ``generation-time`` - the time this response was generated
* ``paragraph ranking algorithm`` - the algorithm used to rank the sentences
* ``sentence ranking algorithm`` - the algorithm used to rank the sentences

Each list entry in ``scored sentences`` contains dictionaries with the following keys:

* ``paragraph score`` - the score of the paragraph as determined by the given algorithm (``readability`` by default)
* ``sentence score`` - the score of the sentence as determiend by the given algorithm (``lede3`` by default)
* ``text`` - the text of the sentence with this score

By default, paragraphs are scored first using the paragraph ranking algorithm and sentences from each paragraph are input into the sentence ranking algorithm. This appears to provide the best results.

Using the HTTP ``Prefer`` header, a client can request different algorithms via the ``algorithm`` preference, like so::

    GET /services/memento/sentencerank/https://www.webarchive.org.uk/wayback/archive/20090522221251/http://blasttheory.co.uk/ HTTP/1.1
    Host: localhost:5000
    User-Agent: curl/7.54.0
    Accept: */*
    Prefer: algorithm=readability/textrank

MementoEmbed responds with the algorithm applied via the ``Preference-Applied`` HTTP response header::

    HTTP/1.0 200 OK
    Content-Type: application/json
    Content-Length: 9547
    Preference-Applied: algorithm=readability/textrank
    Server: Werkzeug/0.15.4 Python/3.7.3
    Date: Mon, 03 Jun 2019 21:42:44 GMT

The algorithms are combinations of paragraph ranking and sentence ranking algorithms separated by a ``/``. The following preferences are available for ``algorithm``:

* ``readability/lede3`` - instructs MementoEmbed to score paragraphs via the ``readability`` algorithm (see above) and then rank the sentences by their position in the paragraph
* ``readability/textrank`` - instructs MementoEmbed to score paragraphs via the ``readability`` algorithm and then rank the sentences within each paragraph via  `Barrios et al.'s Summa implementation <https://github.com/summanlp/textrank>`_ of `Mihalcea's Textrank algorithm <http://www.aclweb.org/anthology/W04-3252>`_
* ``justext/textrank`` - instructs MementoEmbed to use the `jusText library <https://pypi.org/project/jusText/>`_ to extract text from the memento and then feed it through ``textrank``; the Textrank scores in this case are built based on the entire document rather than within ranked paragraphs


Product Endpoints for Requesting a Surrogate Directly
-----------------------------------------------------

Social Cards
~~~~~~~~~~~~

Endpoint: ``/services/product/socialcard/<URI-M>``

On success, the social card service produces an HTTP 200 status response containing a social card with a MIME-type of ``text/html``. This HTML is suitable for inclusion into a web page::

    <blockquote
        class="mementoembed"
        data-versionurl="https://www.webarchive.org.uk/wayback/archive/20090522221251/http://blasttheory.co.uk/"
        data-originalurl="http://blasttheory.co.uk/" 
        data-surrogate-creation-time="2018-07-20T16:08:40Z" 
        data-image="https://www.webarchive.org.uk/wayback/archive/20090522221251/http:/blasttheory.co.uk/bt/i/yougetme/ygm_icon.jpg" 
        data-archive-name="WEBARCHIVE.ORG.UK" data-archive-favicon="https://www.webarchive.org.uk/ukwa/static/images/ukwa-icon-16.png" 
        data-archive-uri="https://www.webarchive.org.uk" 
        data-archive-collection-id="None" 
        data-archive-collection-uri="None" 
        data-archive-collection-name="None" 
        data-original-favicon="https://www.blasttheory.co.uk/wp-content/themes/blasttheory/images/bt_icon.ico" 
        data-original-domain="blasttheory.co.uk" 
        data-original-link-status="Live" 
        data-versiondate="2009-05-22 22:12:51 GMT" 
        style="width: 500px; font-size: 12px; border: 1px solid rgb(231, 231, 231);">
        <div class="me-textright">
            <p class="me-title"><a class="me-title-link" href="https://www.webarchive.org.uk/wayback/archive/20090522221251/http://blasttheory.co.uk/">Blast Theory</a>
            </p>
            <p class="me-snippet">Sam Pearson and Clara Garcia Fraile are in residence for one month Sam Pearson and Clara Garcia Fraile are in residence for one month working on a new project called In My Shoes. They are developin
            </p>
            </div>
    </blockquote>
    <script async src="http://mementoembed.ws-dl.cs.odu.edu/static/js/mementoembed-v20180806.js" charset="utf-8"></script>


One could conceivably use the output of this endpoint as an argument to the ``src`` attribute in an HTML ``<iframe>`` tag, but we do not recommend this. The HTML is intended to be downloaded and included separately.

On failure, the thumbnail service produces a response with a MIME-type of ``application/json`` that includes the nature of the failure::

    {

    "content": "<div class=\"row\">\n    <div class=\"col\">\n        <p style=\"text-align: left;\">The URL you supplied ( <a href=\"http://example.com)\">http://example.com</a> ) is not a memento or comes from an archive that is not Memento-Compliant.</p>\n        <p style=\"text-align: left;\">\n            For a live web resource, you can create a memento that resides on the web in the following ways:\n            <ul>\n                <li style=\"text-align: left;\">Using the <a href=\"https://web.archive.org\">Internet Archive's Save Page Now button.</a></li>\n                <!-- <li style=\"text-align: left;\">Saving the web page at Archive.is</li> -->\n                <li style=\"text-align: left;\">Using the <a href=\"https://github.com/oduwsdl/archivenow\">ArchiveNow</a> utility.</li>\n                <li style=\"text-align: left;\">Using a browser plugin, like <a href=\"https://chrome.google.com/webstore/detail/mink-integrate-live-archi/jemoalkmipibchioofomhkgimhofbbem?hl=en-US\">Mink</a>.</li>\n            </ul>\n\n        </p>\n        <p style=\"text-align: center; font-weight: bold;\">Happy Memento Making! \ud83d\ude00</p>\n    </div>\n</div>\n",
    "error details": "'Traceback (most recent call last):\\n  File \"/usr/local/lib/python3.6/site-packages/mementoembed/mementoresource.py\", line 80, in get_memento_datetime_from_response\\n    response.headers[\\'memento-datetime\\'],\\n  File \"/usr/local/lib/python3.6/site-packages/requests/structures.py\", line 54, in __getitem__\\n    return self._store[key.lower()][1]\\nKeyError: \\'memento-datetime\\'\\n\\nDuring handling of the above exception, another exception occurred:\\n\\nTraceback (most recent call last):\\n  File \"/usr/local/lib/python3.6/site-packages/mementoembed/services/errors.py\", line 26, in handle_errors\\n    return function_name(urim)\\n  File \"/usr/local/lib/python3.6/site-packages/mementoembed/services/product.py\", line 57, in generate_socialcard_response\\n    httpcache\\n  File \"/usr/local/lib/python3.6/site-packages/mementoembed/mementosurrogate.py\", line 26, in __init__\\n    self.memento = memento_resource_factory(self.urim, self.httpcache)\\n  File \"/usr/local/lib/python3.6/site-packages/mementoembed/mementoresource.py\", line 222, in memento_resource_factory\\n    memento_dt = get_memento_datetime_from_response(response)\\n  File \"/usr/local/lib/python3.6/site-packages/mementoembed/mementoresource.py\", line 85, in get_memento_datetime_from_response\\n    response=response, original_exception=e)\\nmementoembed.mementoresource.NotAMementoError: no memento-datetime header\\n'"
    }

**Specifying desired options for the social card with HTTP Prefer**

Using the HTTP ``Prefer`` header specified in `RFC 7240 <https://tools.ietf.org/html/rfc7240>`_, a client can request a social card with specific features. For example, this client has contacted MementoEmbed at endpoint ``/services/product/socialcard/``, requesting a social card of URI-M ``http://web.archive.org/web/20180128152127/http://www.cs.odu.edu/~mkelly/`` without including the remote JavaScript can be done as follows::

    GET /services/product/socialcard/http://web.archive.org/web/20180128152127/http://www.cs.odu.edu/~mkelly/ HTTP/1.1
    Host: mementoembed.ws-dl.cs.odu.edu
    User-Agent: curl/7.54.0
    Accept: */*
    Prefer: using_remote_javascript=no

The response from MementoEmbed uses the ``Preference-Applied`` header to indicate which preferences have been applied, as shown in the following headers::

    HTTP/1.0 200 OK
    Content-Type: text/html; charset=utf-8
    Content-Length: 7179
    Preference-Applied: datauri_favicon=no,datauri_image=no,using_remote_javascript=no,minify_markup=yes
    Server: Werkzeug/0.14.1 Python/3.7.0
    Date: Thu, 20 Sep 2018 17:44:34 GMT

    ...7179 bytes of data follows...

MementoEmbed supports a growing list of options for social cards:

* ``datauri_favicon`` - with a value of 'yes', instructs MementoEmbed to return the favicons for the archive and the original resource as data URIs rather than (standard) remote URIs, this option remotes the remote dependency on remote systems that may fail
* ``datauri_image`` - with a value of 'yes', instructs MementoEmbed to return the striking image as a data URI rather than a (standard) remote URI
* ``using_remote_javascript`` - with a value of 'no', instructs MementoEmbed to return a social card without any remote JavaScript calls, removing a dependency on a remote service
* ``minify_markup`` - with a value of 'yes', instructs MementoEmbed to minify the HTML of the social card

Thumbnails
~~~~~~~~~~

Endpoint: ``/services/product/thumbnail/<URI-M>``

On success, the thumbnail service produces an HTTP 200 status response containing a thumbnail with a MIME-type of ``image/png``.

.. image:: images/thumbnail-example.png

On failure, the thumbnail service produces an HTTP 500 status response with a MIME-type of `application/json` that indicates the nature of the failure::

    {
        "error": "a thumbnail failed to generate in 30 seconds",
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

    ...437589 bytes of data follow...

MementoEmbed supports several options for specifying desired options for thumbnails.

The following options are supported:

* ``viewport_width`` - the width of the viewport of the browser capturing the snapshot (upper bound is 5120px)
* ``viewport_height`` - the height of the viewport of the browser capturing the snapshot (upper bound is 2880px)
* ``thumbnail_width`` - the width of the thumbnail in pixels, the thumbnail will be reduced in size to meet this requirement (upper bound is 5210px)
* ``thumbnail_height`` - the height of the thumbnail in pixels, the thumbnail will be reduced in size to meet this requirement (upper bound is 2880px)
* ``timeout`` - how long MementoEmbed should wait for the thumbnail to finish generating before issuing an error (upper bound is 5 minutes)

If the viewport size requested is less than the thumbnail size, the thumbnail size will match the viewport size.

If the thumbnail height is not specified, the ratio of width to height of the viewport will be used to calculate the height of the thumbnail.

Imagereels
~~~~~~~~~~

Endpoint: ``/services/product/imagereel/<URI-M>``

On success, the imagereel service produces an HTTP 200 status response containing an animated GIF with a MIME-type of ``image/gif``.

.. image:: images/imagereel-example.gif

On failure, the thumbnail service produces an HTTP 500 status response with a MIME-type of `application/json` that indicates the nature of the failure::

    {
        "content": "<div class=\"row\">\n    <div class=\"col\">\n        <p style=\"text-align: left;\">The URL you supplied ( <a href=\"https://www.cnn.com)\">https://www.cnn.com</a> ) is not a memento or comes from an archive that is not Memento-Compliant.</p>\n        <p style=\"text-align: left;\">\n            For a live web resource, you can create a memento that resides on the web in the following ways:\n            <ul>\n                <li style=\"text-align: left;\">Using the <a href=\"https://web.archive.org\">Internet Archive's Save Page Now button.</a></li>\n                <!-- <li style=\"text-align: left;\">Saving the web page at Archive.is</li> -->\n                <li style=\"text-align: left;\">Using the <a href=\"https://github.com/oduwsdl/archivenow\">ArchiveNow</a> utility.</li>\n                <li style=\"text-align: left;\">Using a browser plugin, like <a href=\"https://chrome.google.com/webstore/detail/mink-integrate-live-archi/jemoalkmipibchioofomhkgimhofbbem?hl=en-US\">Mink</a>.</li>\n            </ul>\n\n        </p>\n        <p style=\"text-align: center; font-weight: bold;\">Happy Memento Making! \ud83d\ude00</p>\n    </div>\n</div>\n",
        "error details": "'Traceback (most recent call last):\\n  File \"/Volumes/nerfherder External/Unsynced-Projects/MementoEmbed/mementoembed/mementoresource.py\", line 88, in get_memento_datetime_from_response\\n    response.headers[\\'memento-datetime\\'],\\n  File \"/Users/smj/.virtualenvs/MementoEmbed/lib/python3.7/site-packages/requests/structures.py\", line 52, in __getitem__\\n    return self._store[key.lower()][1]\\nKeyError: \\'memento-datetime\\'\\n\\nDuring handling of the above exception, another exception occurred:\\n\\nTraceback (most recent call last):\\n  File \"/Volumes/nerfherder External/Unsynced-Projects/MementoEmbed/mementoembed/services/errors.py\", line 28, in handle_errors\\n    return function_name(urim, preferences)\\n  File \"/Volumes/nerfherder External/Unsynced-Projects/MementoEmbed/mementoembed/services/product.py\", line 185, in generate_imagereel_response\\n    int(prefs[\\'height\\'])\\n  File \"/Volumes/nerfherder External/Unsynced-Projects/MementoEmbed/mementoembed/mementoimagereel.py\", line 36, in generate_imagereel\\n    memento = memento_resource_factory(urim, self.httpcache)\\n  File \"/Volumes/nerfherder External/Unsynced-Projects/MementoEmbed/mementoembed/mementoresource.py\", line 240, in memento_resource_factory\\n    memento_dt = get_memento_datetime_from_response(response)\\n  File \"/Volumes/nerfherder External/Unsynced-Projects/MementoEmbed/mementoembed/mementoresource.py\", line 99, in get_memento_datetime_from_response\\n    response=response, original_exception=e)\\nmementoembed.mementoresource.NotAMementoError: no memento-datetime header\\n'"
    }

This response contains two keys:

* ``error`` - this provides an explanation of the failure
* ``error details`` - this provides a Traceback of the MementoEmbed application that may be useful for diagnosing the error if it is a failure in the application

**Specifying desired options for the imagreel with HTTP Prefer**

Using the HTTP ``Prefer`` header specified in `RFC 7240 <https://tools.ietf.org/html/rfc7240>`_, a client can request a thumbnail with specific features. For example, this client has contacted MementoEmbed at endpoint ``/services/product/thumbnail/``, requesting a thumbnail of URI-M ``http://web.archive.org/web/20180128152127/http://www.cs.odu.edu/~mkelly/`` with a viewport width of 4096 pixels and a thumbnail width of 2048 pixels::

    GET /services/product/imagereel/https://wayback.archive-it.org/2358/20110211072257/http://news.blogs.cnn.com/category/world/egypt-world-latest-news/ HTTP/1.1
    Host: mementoembed.ws-dl.cs.odu.edu
    User-Agent: curl/7.54.0
    Accept: */*
    Prefer: width=320,height=240

The response from MementoEmbed uses the ``Preference-Applied`` header to indicate which preferences have been applied, as shown in the following headers::

    HTTP/1.0 200 OK
    Content-Type: image/gif
    Content-Length: 3275339
    Preference-Applied: duration=100,imagecount=5,width=320,height=240
    Server: Werkzeug/0.15.4 Python/3.7.3
    Date: Mon, 03 Jun 2019 21:21:34 GMT

    ...3275339 bytes of data follow...

MementoEmbed supports several options for specifying desired options for thumbnails.

The following options are supported:

* ``duration`` - the number of milliseconds for each frame of the animated GIF
* ``imagecount`` - the number of images to include in the imagereel
* ``width`` - the width of the imagereel in pixels
* ``height`` - the height of the imagereel in pixels

If the imagereel height is not specified, the ratio of width to height of the viewport will be used to calculate the height of the thumbnail.
