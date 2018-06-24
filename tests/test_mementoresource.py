import os
import unittest
import zipfile
import io

from datetime import datetime

from mementoembed.mementoresource import MementoResource, WaybackMemento, \
    IMFMemento, ArchiveIsMemento, memento_resource_factory

testdir = os.path.dirname(os.path.realpath(__file__))

class mock_response:

    def __init__(self, headers, text, status, content=None):
        self.headers = headers
        self.text = text
        
        if content is None:

            if type(content) == str:
                self.content = bytes(text.encode('utf-8'))
            else:
                self.content = content

        else:
            self.content = content

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

class TestMementoResource(unittest.TestCase):

    def test_simplecase(self):

        urim = "http://myarchive.org/memento/http://example.com/something"
        expected_urig = "http://myarchive.org/timegate/http://example.com/something"
        expected_original_uri = "http://example.com/something"

        expected_content = """
        <html>
            <head>
                <title>Is this a good title?</title>
            </head>
            <body>
                Is this good text?
            </body>
        </html>"""

        cachedict = {
            urim:
                mock_response(
                    headers = {
                        'memento-datetime': "Fri, 22 Jun 2018 21:16:36 GMT",
                        'link': """<{}>; rel="original", 
                            <{}>; rel="timegate",
                            <http://myarchive.org/timemap/http://example.com/something>; rel="timemap",
                            <{}>; rel="memento"
                            """.format(expected_original_uri, expected_urig, urim)
                    },
                    text = expected_content,
                    status=200
                )
        }

        mh = mock_httpcache(cachedict)

        mr = memento_resource_factory(urim, mh)

        expected_mdt = datetime.strptime(
            "Fri, 22 Jun 2018 21:16:36 GMT", 
            "%a, %d %b %Y %H:%M:%S GMT"
        )

        self.assertEqual(type(mr), MementoResource)

        self.assertEqual(mr.memento_datetime, expected_mdt)
        self.assertEqual(mr.timegate, expected_urig)
        self.assertEqual(mr.original_uri, expected_original_uri)
        self.assertEqual(mr.content, expected_content)
        self.assertEqual(mr.raw_content, expected_content)

    def test_waybackcase(self):

        urim = "http://myarchive.org/memento/20080202062913/http://example.com/something"
        raw_urim = "http://myarchive.org/memento/20080202062913id_/http://example.com/something"
        expected_urig = "http://myarchive.org/timegate/http://example.com/something"
        expected_original_uri = "http://example.com/something"

        expected_content = """
        <html>
            <head>
                <title>Is this a good title?</title>
            </head>
            <body>
                <!-- ARCHIVE SPECIFIC STUFF -->
                Is this good text?
            </body>
        </html>"""

        expected_raw_content = """
        <html>
            <head>
                <title>Is this a good title?</title>
            </head>
            <body>
                Is this good text?
            </body>
        </html>"""

        cachedict = {
            urim:
                mock_response(
                    headers = {
                        'memento-datetime': "Sat, 02 Feb 2008 06:29:13 GMT",
                        'link': """<{}>; rel="original", 
                            <{}>; rel="timegate",
                            <http://myarchive.org/timemap/http://example.com/something>; rel="timemap",
                            <{}>; rel="memento"
                            """.format(expected_original_uri, expected_urig, urim)
                    },
                    text = expected_content,
                    status=200
                ),
            raw_urim:
                mock_response(
                    headers = {},
                    text = expected_raw_content,
                    status=200
                )
        }

        mh = mock_httpcache(cachedict)

        mr = memento_resource_factory(urim, mh)

        expected_mdt = datetime.strptime(
            "Sat, 02 Feb 2008 06:29:13 GMT", 
            "%a, %d %b %Y %H:%M:%S GMT"
        )

        self.assertEqual(type(mr), WaybackMemento)

        self.assertEqual(mr.memento_datetime, expected_mdt)
        self.assertEqual(mr.timegate, expected_urig)
        self.assertEqual(mr.original_uri, expected_original_uri)
        self.assertEqual(mr.content, expected_content)
        self.assertEqual(mr.raw_content, expected_raw_content)

    def test_imfcase(self):

        urim = "http://myarchive.org/memento/notraw/http://example.com/something"
        raw_urim = "http://myarchive.org/memento/raw/http://example.com/something"
        expected_urig = "http://myarchive.org/timegate/http://example.com/something"
        expected_original_uri = "http://example.com/something"

        expected_content = """
        <html>
            <head>
                <title>ARCHIVED: Is this a good title?</title>
            </head>
            <body>
                <p>Some Archive-specific stuff here</p>
                <iframe id="theWebpage" src="{}"></iframe>
            </body>
        </html>""".format(raw_urim)

        expected_raw_content = """
        <html>
            <head>
                <title>Is this a good title?</title>
            </head>
            <body>
                Is this good text?
            </body>
        </html>"""

        cachedict = {
            urim:
                mock_response(
                    headers = {
                        'memento-datetime': "Sat, 02 Feb 2008 06:29:13 GMT",
                        'link': """<{}>; rel="original", 
                            <{}>; rel="timegate",
                            <http://myarchive.org/timemap/http://example.com/something>; rel="timemap",
                            <{}>; rel="memento"
                            """.format(expected_original_uri, expected_urig, urim)
                    },
                    text = expected_content,
                    status=200
                ),
            raw_urim:
                mock_response(
                    headers = {},
                    text = expected_raw_content,
                    status=200
                )
        }

        mh = mock_httpcache(cachedict)

        mr = memento_resource_factory(urim, mh)

        expected_mdt = datetime.strptime(
            "Sat, 02 Feb 2008 06:29:13 GMT", 
            "%a, %d %b %Y %H:%M:%S GMT"
        )

        self.assertEqual(type(mr), IMFMemento)

        self.assertEqual(mr.memento_datetime, expected_mdt)
        self.assertEqual(mr.timegate, expected_urig)
        self.assertEqual(mr.original_uri, expected_original_uri)
        self.assertEqual(mr.content, expected_content)
        self.assertEqual(mr.raw_content, expected_raw_content)

    def test_archiveiscase(self):

        urim = "http://archive.is/abcd1234"
        zipurim = "http://archive.is/download/abcd1234.zip"
        expected_original_uri = "http://example.com/something"
        expected_urig = "http://myarchive.org/timegate/http://example.com/something"
        

        expected_raw_content = """
        <html>
            <head>
                <title>Is this a good title?</title>
            </head>
            <body>
                Is this good text?
            </body>
        </html>"""

        expected_content = """
        <html>
            <head>
                <title>ARCHIVED: Is this a good title?</title>
            </head>
            <body>
                <p>Some Archive-specific stuff here</p>
                <div id="SOLID">{}</div>
            </body>
        </html>""".format(expected_raw_content)


        file_like_object = io.BytesIO()
        zf = zipfile.ZipFile(file_like_object, mode='w')

        zf.writestr('index.html', expected_raw_content)
        zf.close()

        zip_content = file_like_object.getvalue()

        cachedict = {
            urim:
                mock_response(
                    headers = {
                        'memento-datetime': "Sat, 02 Feb 2008 06:29:13 GMT",
                        'link': """<{}>; rel="original", 
                            <{}>; rel="timegate",
                            <http://myarchive.org/timemap/http://example.com/something>; rel="timemap",
                            <{}>; rel="memento"
                            """.format(expected_original_uri, expected_urig, urim)
                    },
                    text = expected_content,
                    status=200
                ),
            zipurim:
                mock_response(
                    headers = {},
                    text = "",
                    content = zip_content,
                    status=200
                )
        }

        mh = mock_httpcache(cachedict)

        mr = memento_resource_factory(urim, mh)

        expected_mdt = datetime.strptime(
            "Sat, 02 Feb 2008 06:29:13 GMT", 
            "%a, %d %b %Y %H:%M:%S GMT"
        )

        self.maxDiff = None

        self.assertEqual(type(mr), ArchiveIsMemento)

        self.assertEqual(mr.memento_datetime, expected_mdt)
        self.assertEqual(mr.timegate, expected_urig)
        self.assertEqual(mr.original_uri, expected_original_uri)
        self.assertEqual(mr.content, expected_content)
        self.assertEqual(mr.raw_content, bytes(expected_raw_content.encode('utf-8')))


    def test_archiveiscase_datetime_in_uri(self):

        urim = "http://archive.is/20130508132946/http://flexispy.com/"
        zipurim = "http://archive.is/download/pSSpa.zip"
        expected_original_uri = "http://flexispy.com/"
        expected_urig = "http://archive.is/timegate/http://flexispy.com/"

        with open("{}/samples/archive.is-1.html".format(testdir), 'rb') as f:
            expected_content = f.read()

        with open("{}/samples/archive.is-1.raw.zip".format(testdir), 'rb') as f:
            zip_content = f.read()

            zf = zipfile.ZipFile(f)
            expected_raw_content = zf.read("index.html")

        cachedict = {
            urim:
                mock_response(
                    headers = {
                        'memento-datetime': "Sat, 02 Feb 2008 06:29:13 GMT",
                        'link': """<{}>; rel="original", 
                            <{}>; rel="timegate",
                            <http://myarchive.org/timemap/http://example.com/something>; rel="timemap",
                            <{}>; rel="memento"
                            """.format(expected_original_uri, expected_urig, urim)
                    },
                    text = expected_content,
                    status=200
                ),
            "http://archive.is/20130508132946id_/http://flexispy.com/":
                mock_response(
                    headers = {},
                    text= "",
                    status=404
                ),
            zipurim:
                mock_response(
                    headers = {},
                    text = "",
                    content = zip_content,
                    status=200
                )
        }

        mh = mock_httpcache(cachedict)

        mr = memento_resource_factory(urim, mh)

        expected_mdt = datetime.strptime(
            "Sat, 02 Feb 2008 06:29:13 GMT", 
            "%a, %d %b %Y %H:%M:%S GMT"
        )

        self.maxDiff = None

        self.assertEqual(type(mr), ArchiveIsMemento)

        self.assertEqual(mr.memento_datetime, expected_mdt)
        self.assertEqual(mr.timegate, expected_urig)
        self.assertEqual(mr.original_uri, expected_original_uri)
        self.assertEqual(mr.content, expected_content)
        self.assertEqual(mr.raw_content, expected_raw_content)
