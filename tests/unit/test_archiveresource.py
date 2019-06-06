import os
import shutil
import zipfile
import unittest

import requests
import requests_cache

from mementoembed.archiveresource import ArchiveResource
from mementoembed.version import __useragent__

cachefile = "{}/test_cache".format(os.path.dirname(os.path.realpath(__file__)))

class mock_response:

    def __init__(self, headers, content, status, url):
        self.headers = headers
        self.content = content
        self.text = bytes(content.encode('utf-8'))
        self.status_code = status
        self.url = url

class mock_httpcache:
    """
        rather than hitting the actual HTTP cache,
        we can simulate behavior for this test
    """

    def __init__(self, cachedict):
        self.cachedict = cachedict

    def get(self, uri, use_referrer=True):
        return self.cachedict[uri]

class TestArchiveResource(unittest.TestCase):

    def test_simplestuff(self):

        httpcache = None
        urim = "https://myarchive.org/somememento"

        x = ArchiveResource(urim, httpcache)

        self.assertEqual(x.scheme, "https")
        self.assertEqual(x.domain, "myarchive.org")
        self.assertEqual(x.name, "MYARCHIVE.ORG")
        self.assertEqual(x.uri, "https://myarchive.org")

    # @unittest.skip("this needs to be updated for the way aiu works now")
    def test_collection_data_extraction(self):

        urim = "http://wayback.archive-it.org/5728/20160518000858/http://blog.willamette.edu/mba/"

        requests_cache.install_cache(cachefile)
        httpcache = requests.Session()
        httpcache.headers.update({'User-Agent': __useragent__})

        x = ArchiveResource(urim, httpcache)
        self.assertEqual(x.scheme, "http")
        self.assertEqual(x.domain, "wayback.archive-it.org")
        self.assertEqual(x.name, "ARCHIVE-IT.ORG")
        self.assertEqual(x.uri, "http://wayback.archive-it.org")
        self.assertEqual(x.home_uri, "https://archive-it.org")

        self.assertEqual(x.collection_id, "5728")
        self.assertEqual(x.collection_uri, "https://archive-it.org/collections/5728")
        self.assertEqual(x.collection_name, "Social Media")
        
    def test_favicon_from_html(self):

        expected_favicon = "http://myarchive.org/content/favicon.ico"

        cachedict = {
            "http://myarchive.org":
                mock_response(
                    headers={},
                    content="""<html>
                    <head>
                        <title>Is this a good title?</title>
                        <link rel="icon" href="{}">
                    </head>
                    <body>Is this all there is to content?</body>
                    </html>""".format(expected_favicon),
                    status=200,
                    url = "testing-url://notused"
                ),
            expected_favicon:
                mock_response(
                    headers = { 'content-type': 'image/x-testing'},
                    content = "a",
                    status=200,
                    url = "testing-url://notused"
                )
        }

        httpcache = mock_httpcache(cachedict)

        urim = "http://myarchive.org/20160518000858/http://example.com/somecontent"

        x = ArchiveResource(urim, httpcache)

        self.assertEqual(x.favicon, expected_favicon)

    def test_404_favicon_from_html_so_constructed_favicon_uri(self):

        expected_favicon = "http://myarchive.org/favicon.ico"

        cachedict = {
            "http://myarchive.org":
                mock_response(
                    headers={},
                    content="""<html>
                    <head>
                        <title>Is this a good title?</title>
                        <link rel="icon" href="http://myarchive.org/content/favicon.ico">
                    </head>
                    <body>Is this all there is to content?</body>
                    </html>""",
                    status=200,
                    url = "testing-url://notused"
                ),
            "http://myarchive.org/content/favicon.ico":
                mock_response(
                    headers = {},
                    content = "",
                    status=404,
                    url = "testing-url://notused"
                ),
            expected_favicon:
                mock_response(
                    headers = { 'content-type': 'image/x-testing'},
                    content = "a",
                    status=200,
                    url = "testing-url://notused"
                )
        }
        
        httpcache = mock_httpcache(cachedict)

        urim = "http://myarchive.org/20160518000858/http://example.com/somecontent"

        x = ArchiveResource(urim, httpcache)

        self.assertEqual(x.favicon, expected_favicon)

    def test_404_favicon_from_constructed_favicon_uri_so_google_service(self):

        expected_favicon = "https://www.google.com/s2/favicons?domain={}".format("myarchive.org")

        cachedict = {
            "http://myarchive.org":
                mock_response(
                    headers={},
                    content="""<html>
                    <head>
                        <title>Is this a good title?</title>
                        <link rel="icon" href="http://myarchive.org/content/favicon.ico">
                    </head>
                    <body>Is this all there is to content?</body>
                    </html>""",
                    status=200,
                    url = "testing-url://notused"
                ),
            "http://myarchive.org/content/favicon.ico":
                mock_response(
                    headers = {},
                    content = "",
                    status=404,
                    url = "testing-url://notused"
                ),
            "http://myarchive.org/favicon.ico":
                mock_response(
                    headers = {
                        'content-type': 'image/x-testing'
                    },
                    content = "",
                    status=404,
                    url = "testing-url://notused"
                ),
            expected_favicon:
                mock_response(
                    headers = { 'content-type': 'image/x-testing'},
                    content = "a",
                    status=200,
                    url = "testing-url://notused"
                )
        }
        
        httpcache = mock_httpcache(cachedict)

        urim = "http://myarchive.org/20160518000858/http://example.com/somecontent"

        x = ArchiveResource(urim, httpcache)

        self.assertEqual(x.favicon, expected_favicon)

    def test_no_good_favicon(self):

        expected_favicon = None

        cachedict = {
            "http://myarchive.org":
                mock_response(
                    headers={},
                    content="""<html>
                    <head>
                        <title>Is this a good title?</title>
                        <link rel="icon" href="http://myarchive.org/content/favicon.ico">
                    </head>
                    <body>Is this all there is to content?</body>
                    </html>""",
                    status=200,
                    url = "testing-url://notused"
                ),
            "http://myarchive.org/content/favicon.ico":
                mock_response(
                    headers = {},
                    content = "",
                    status=404,
                    url = "testing-url://notused"
                ),
            "http://myarchive.org/favicon.ico":
                mock_response(
                    headers = {
                        'content-type': 'image/x-testing'
                    },
                    content = "",
                    status=404,
                    url = "testing-url://notused"
                ),
            "https://www.google.com/s2/favicons?domain={}".format("myarchive.org"):
                mock_response(
                    headers = {},
                    content = "",
                    status=404,
                    url = "testing-url://notused"
                )
        }
        
        httpcache = mock_httpcache(cachedict)

        urim = "http://myarchive.org/20160518000858/http://example.com/somecontent"

        x = ArchiveResource(urim, httpcache)

        self.assertEqual(x.favicon, expected_favicon)

    def test_favicon_from_html_relative_uri(self):

        expected_favicon = "http://myarchive.org/content/favicon.ico"

        cachedict = {
            "http://myarchive.org":
                mock_response(
                    headers={},
                    content="""<html>
                    <head>
                        <title>Is this a good title?</title>
                        <link rel="icon" href="content/favicon.ico">
                    </head>
                    <body>Is this all there is to content?</body>
                    </html>""",
                    status=200,
                    url = "testing-url://notused"
                ),
            expected_favicon:
                mock_response(
                    headers = { 'content-type': 'image/x-testing'},
                    content = "a",
                    status=200,
                    url = "testing-url://notused"
                )
        }

        httpcache = mock_httpcache(cachedict)

        urim = "http://myarchive.org/20160518000858/http://example.com/somecontent"

        x = ArchiveResource(urim, httpcache)

        self.assertEqual(x.favicon, expected_favicon)

    def test_link_tag_no_rel(self):

        expected_favicon = None

        cachedict = {
            "http://myarchive.org":
                mock_response(
                    headers={},
                    content="""<html>
                    <head>
                        <title>Is this a good title?</title>
                        <link title="a good title" href="content/favicon.ico">
                    </head>
                    <body>Is this all there is to content?</body>
                    </html>""",
                    status=200,
                    url = "testing-url://notused"
                ),
            expected_favicon:
                mock_response(
                    headers = { 'content-type': 'image/x-testing'},
                    content = "a",
                    status=200,
                    url = "testing-url://notused"
                ),
            "http://myarchive.org/favicon.ico":
                mock_response(
                    headers={},
                    content="not found",
                    status=404,
                    url="testing-url://notused"
                ),
            "https://www.google.com/s2/favicons?domain=myarchive.org":
                mock_response(
                    headers={},
                    content="not found",
                    status=404,
                    url="testing-url://notused"
                )
        }

        httpcache = mock_httpcache(cachedict)

        urim = "http://myarchive.org/20160518000858/http://example.com/somecontent"

        x = ArchiveResource(urim, httpcache)

        self.assertEqual(x.favicon, expected_favicon)
