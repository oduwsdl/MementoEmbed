import os
import shutil
import zipfile
import unittest

from mementoembed.archiveresource import ArchiveResource

class mock_response:

    def __init__(self, headers, content, status):
        self.headers = headers
        self.content = content
        self.text = bytes(content.encode('utf-8'))
        self.status_code = status

class mock_httpcache:
    """
        rather than hitting the actual HTTP cache,
        we can simulate behavior for this test
    """

    def __init__(self, cachedict):
        self.cachedict = cachedict

    def get(self, uri):
        return self.cachedict[uri]

    def is_uri_good(self, uri):

        if self.cachedict[uri].status_code == 200:
            return True
        else:
            return False

class TestArchiveResource(unittest.TestCase):

    def test_simplestuff(self):

        httpcache = None
        urim = "https://myarchive.org/somememento"
        working_directory = "/tmp/{}".format(os.path.basename(__file__))

        x = ArchiveResource(urim, httpcache, working_directory)

        self.assertEqual(x.scheme, "https")
        self.assertEqual(x.domain, "myarchive.org")
        self.assertEqual(x.name, "MYARCHIVE.ORG")
        self.assertEqual(x.uri, "https://myarchive.org")

        if os.path.exists(working_directory):
            shutil.rmtree(working_directory)

    def test_collection_data_extraction(self):

        # uncompress collection data into a working directory
        working_directory = "/tmp/{}".format(os.path.basename(__file__))
        urim = "http://wayback.archive-it.org/5728/20160518000858/http://blog.willamette.edu/mba/"
        httpcache = None

        if not os.path.exists(working_directory):
            os.makedirs(working_directory)

        testdatafile = "{}/samples/ac5728.zip".format(
            os.path.dirname(os.path.realpath(__file__))
        )

        zipref = zipfile.ZipFile(testdatafile, 'r')
        zipref.extractall(working_directory)
        zipref.close()

        x = ArchiveResource(urim, httpcache, working_directory)
        self.assertEqual(x.scheme, "http")
        self.assertEqual(x.domain, "wayback.archive-it.org")
        self.assertEqual(x.name, "Archive-It")
        self.assertEqual(x.uri, "http://wayback.archive-it.org")
        self.assertEqual(x.home_uri, "https://archive-it.org")

        self.assertEqual(x.collection_id, "5728")
        self.assertEqual(x.collection_uri, "https://archive-it.org/collections/5728")
        self.assertEqual(x.collection_name, "Social Media")

        shutil.rmtree(working_directory)
        
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
                    status=200
                ),
            expected_favicon:
                mock_response(
                    headers = { 'content-type': 'image/x-testing'},
                    content = "",
                    status=200
                )
        }

        httpcache = mock_httpcache(cachedict)
        working_directory = "/tmp/{}".format(os.path.basename(__file__))

        urim = "http://myarchive.org/20160518000858/http://example.com/somecontent"

        x = ArchiveResource(urim, httpcache, working_directory)

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
                    status=200
                ),
            "http://myarchive.org/content/favicon.ico":
                mock_response(
                    headers = {},
                    content = "",
                    status=404
                ),
            expected_favicon:
                mock_response(
                    headers = { 'content-type': 'image/x-testing'},
                    content = "a",
                    status=200
                )
        }
        
        working_directory = "/tmp/{}".format(os.path.basename(__file__))
        httpcache = mock_httpcache(cachedict)

        urim = "http://myarchive.org/20160518000858/http://example.com/somecontent"

        x = ArchiveResource(urim, httpcache, working_directory)

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
                    status=200
                ),
            "http://myarchive.org/content/favicon.ico":
                mock_response(
                    headers = {},
                    content = "",
                    status=404
                ),
            "http://myarchive.org/favicon.ico":
                mock_response(
                    headers = {
                        'content-type': 'image/x-testing'
                    },
                    content = "",
                    status=404
                ),
            expected_favicon:
                mock_response(
                    headers = { 'content-type': 'image/x-testing'},
                    content = "a",
                    status=200
                )
        }
        
        working_directory = "/tmp/{}".format(os.path.basename(__file__))
        httpcache = mock_httpcache(cachedict)

        urim = "http://myarchive.org/20160518000858/http://example.com/somecontent"

        x = ArchiveResource(urim, httpcache, working_directory)

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
                    status=200
                ),
            "http://myarchive.org/content/favicon.ico":
                mock_response(
                    headers = {},
                    content = "",
                    status=404
                ),
            "http://myarchive.org/favicon.ico":
                mock_response(
                    headers = {
                        'content-type': 'image/x-testing'
                    },
                    content = "",
                    status=404
                ),
            "https://www.google.com/s2/favicons?domain={}".format("myarchive.org"):
                mock_response(
                    headers = {},
                    content = "",
                    status=404
                )
        }
        
        working_directory = "/tmp/{}".format(os.path.basename(__file__))
        httpcache = mock_httpcache(cachedict)

        urim = "http://myarchive.org/20160518000858/http://example.com/somecontent"

        x = ArchiveResource(urim, httpcache, working_directory)

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
                    status=200
                ),
            expected_favicon:
                mock_response(
                    headers = { 'content-type': 'image/x-testing'},
                    content = "",
                    status=200
                )
        }

        httpcache = mock_httpcache(cachedict)
        working_directory = "/tmp/{}".format(os.path.basename(__file__))

        urim = "http://myarchive.org/20160518000858/http://example.com/somecontent"

        x = ArchiveResource(urim, httpcache, working_directory)

        self.assertEqual(x.favicon, expected_favicon)
