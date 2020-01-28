import os
import unittest
import zipfile
import io

from datetime import datetime
from urllib.parse import urljoin

from mementoembed.mementoresource import MementoResource, WaybackMemento, \
    IMFMemento, ArchiveIsMemento, memento_resource_factory, NotAMementoError

testdir = os.path.dirname(os.path.realpath(__file__))

class mock_response:

    def __init__(self, headers, text, status, url, content=None, links={}):
        self.headers = headers
        self.text = text
        self.url = url
        self.links = links
        self.history = []
        
        if content is None:

            if type(content) == str:
                self.content = bytes(text.encode('utf-8'))
            else:
                self.content = content

        else:
            self.content = content

        self.status_code = status

        class mock_request:

            def __init__(self):
                self.url = "mock_request url"
                self.headers = {}

        self.request = mock_request()

class mock_httpcache:
    """
        rather than hitting the actual HTTP cache,
        we can simulate behavior for this test
    """

    def __init__(self, cachedict):
        self.cachedict = cachedict

    def get(self, uri, **args):
        return self.cachedict[uri]

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
                        'content-type': 'text/html',
                        'memento-datetime': "Fri, 22 Jun 2018 21:16:36 GMT",
                        'link': """<{}>; rel="original", 
                            <{}>; rel="timegate",
                            <http://myarchive.org/timemap/http://example.com/something>; rel="timemap",
                            <{}>; rel="memento"
                            """.format(expected_original_uri, expected_urig, urim)
                    },
                    text = expected_content,
                    status=200,
                    url = urim,
                    links = {
                        "original": {
                            "url": expected_original_uri
                        },
                        "timegate": {
                            "url": expected_urig
                        }
                    }
                ),
            expected_urig: # requests follows all redirects, so we present the result at the end of the chain
                mock_response(
                    headers = {
                        'content-type': 'text/html',
                        'memento-datetime': "Fri, 22 Jun 2018 21:16:36 GMT",
                        'link': """<{}>; rel="original", 
                            <{}>; rel="timegate",
                            <http://myarchive.org/timemap/http://example.com/something>; rel="timemap",
                            <{}>; rel="memento"
                            """.format(expected_original_uri, expected_urig, urim)
                    },
                    text = expected_content,
                    status=200,
                    url = urim,
                    links = {
                        "original": {
                            "url": expected_original_uri
                        },
                        "timegate": {
                            "url": expected_urig
                        }
                    }
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
                        'content-type': 'text/html',
                        'memento-datetime': "Sat, 02 Feb 2008 06:29:13 GMT",
                        'link': """<{}>; rel="original", 
                            <{}>; rel="timegate",
                            <http://myarchive.org/timemap/http://example.com/something>; rel="timemap",
                            <{}>; rel="memento"
                            """.format(expected_original_uri, expected_urig, urim)
                    },
                    text = expected_content,
                    status=200,
                    url = urim,
                    links = {
                        "original": {
                            "url": expected_original_uri
                        },
                        "timegate": {
                            "url": expected_urig
                        }
                    }
                ),
            raw_urim:
                mock_response(
                    headers = {
                        'content-type': 'text/html'
                    },
                    text = expected_raw_content,
                    status=200,
                    url = raw_urim
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
                        'content-type': 'text/html',
                        'memento-datetime': "Sat, 02 Feb 2008 06:29:13 GMT",
                        'link': """<{}>; rel="original", 
                            <{}>; rel="timegate",
                            <http://myarchive.org/timemap/http://example.com/something>; rel="timemap",
                            <{}>; rel="memento"
                            """.format(expected_original_uri, expected_urig, urim)
                    },
                    text = expected_content,
                    status=200,
                    url = urim,
                    links = {
                        "original": {
                            "url": expected_original_uri
                        },
                        "timegate": {
                            "url": expected_urig
                        }
                    }
                ),
            raw_urim:
                mock_response(
                    headers = {
                        'content-type': 'text/html'
                    },
                    text = expected_raw_content,
                    status=200,
                    url = raw_urim
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
                        'content-type': 'text/html',
                        'memento-datetime': "Sat, 02 Feb 2008 06:29:13 GMT",
                        'link': """<{}>; rel="original", 
                            <{}>; rel="timegate",
                            <http://myarchive.org/timemap/http://example.com/something>; rel="timemap",
                            <{}>; rel="memento"
                            """.format(expected_original_uri, expected_urig, urim)
                    },
                    text = expected_content,
                    status=200,
                    url = urim,
                    links = {
                        "original": {
                            "url": expected_original_uri
                        },
                        "timegate": {
                            "url": expected_urig
                        }
                    }
                ),
            zipurim:
                mock_response(
                    headers = {
                        'content-type': 'text/html'
                    },
                    text = "",
                    content = zip_content,
                    status=200,
                    url = zipurim
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

    def test_bad_headers(self):

        urim = "http://myarchive.org/memento/20080202062913/http://example.com/something"
        raw_urim = "http://myarchive.org/memento/20080202062913id_/http://example.com/something"
        urir = "http://example.com/something"
        expected_urig = "http://myarchive.org/timegate/http://example.com/something"

        content = """
        <html>
            <head>
                <title>Is this a good title?</title>
            </head>
                <!-- ARCHIVE SPECIFIC STUFF -->
                <frameset rows="*" cols="130,*" framespacing="0" border="0">
                    <frame src="frame1.htm">
                    <frame src="pages/frame2.htm">
                    <frame src="/content/frame3.htm">
                    <frame src="http://example2.com/content/frame4.htm">
                </frameset>
        </html>"""

        cachedict = {
            urim:
                mock_response(
                    headers = {
                        'link': """<{}>; rel="original", 
                            <{}>; rel="timegate",
                            <http://myarchive.org/timemap/http://example.com/something>; rel="timemap",
                            <{}>; rel="memento"
                            """.format(urir, expected_urig, urim)
                    },
                    text = content,
                    status=200,
                    url = urim
                ),
            raw_urim:
                mock_response(
                    headers = {},
                    text = "",
                    status = 404,
                    url = raw_urim
                )
        }

        mh = mock_httpcache(cachedict)

        self.assertRaises( NotAMementoError, memento_resource_factory, urim, mh )

        cachedict = {
            urim:
                mock_response(
                    headers = {
                        'content-type': 'text/html',
                        'memento-datetime': "Sat, 02 Feb 2008 06:29:13 GMT",
                        'link': """<{}>; rel="timegate",
                            <http://myarchive.org/timemap/http://example.com/something>; rel="timemap",
                            <{}>; rel="memento"
                            """.format(expected_urig, urim)
                    },
                    text = content,
                    status=200,
                    url = urim
                ),
            raw_urim:
                mock_response(
                    headers = {},
                    text = "",
                    status = 404,
                    url = raw_urim
                )
        }

        mh = mock_httpcache(cachedict)

        self.assertRaises( NotAMementoError, memento_resource_factory, urim, mh )

        cachedict = {
            urim:
                mock_response(
                    headers = {
                        'memento-datetime': "Sat, 02 Feb 2008 06:29:13 GMT"
                        },
                    text = content,
                    status=200,
                    url = urim
                ),
            raw_urim:
                mock_response(
                    headers = {},
                    text = "",
                    status = 404,
                    url = raw_urim
                )
        }

        mh = mock_httpcache(cachedict)

        self.assertRaises( NotAMementoError, memento_resource_factory, urim, mh )

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
                        'content-type': 'text/html',
                        'memento-datetime': "Sat, 02 Feb 2008 06:29:13 GMT",
                        'link': """<{}>; rel="original", 
                            <{}>; rel="timegate",
                            <http://myarchive.org/timemap/http://example.com/something>; rel="timemap",
                            <{}>; rel="memento"
                            """.format(expected_original_uri, expected_urig, urim)
                    },
                    text = expected_content,
                    status=200,
                    url = urim,
                    links = {
                        "original": {
                            "url": expected_original_uri
                        },
                        "timegate": {
                            "url": expected_urig
                        }
                    }
                ),
            "http://archive.is/20130508132946id_/http://flexispy.com/":
                mock_response(
                    headers = {},
                    text= "",
                    status=404,
                    url = "http://archive.is/20130508132946id_/http://flexispy.com/"
                ),
            zipurim:
                mock_response(
                    headers = {
                        'content-type': 'text/html',
                    },
                    text = "",
                    content = zip_content,
                    status=200,
                    url = zipurim
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

    def test_meta_redirect(self):

        urim = "https://archive-example.org/web/20180401102030/http://example.com/redirpage"
        redirurim = "https://archive-example.org/web/20180308084654/http://example.com/testpage"

        metaredirecthtml="""<html>
<meta http-equiv="refresh" content="0; URL='{}'"/>
</html>""".format(redirurim)

        expected_content = "<html><body>somecontent</body></html>"
        expected_raw_content = expected_content

        expected_original_uri = "http://example.com/redirpage"
        expected_urig = "https://archive-example.org/web/timegate/http://example.com/redirpage"

        redir_expected_original_uri = "http://example.com/testpage"
        redir_expected_urig = "https://archive-example.org/web/timegate/http://example.com/testpage"

        redirurim_raw = "https://archive-example.org/web/20180308084654id_/http://example.com/testpage"
        expected_raw_content = "<html><body>raw content</body></html>"

        cachedict = {
            urim:
                mock_response(
                    headers = {
                        'content-type': 'text/html',
                        'memento-datetime': "Sat, 02 Feb 2008 06:29:13 GMT",
                        'link': """<{}>; rel="original", 
                            <{}>; rel="timegate",
                            <http://myarchive.org/timemap/http://example.com/something>; rel="timemap",
                            <{}>; rel="memento"
                            """.format(expected_original_uri, expected_urig, urim)
                    },
                    text = metaredirecthtml,
                    content = metaredirecthtml,
                    status = 200,
                    url = urim,
                    links = {
                        "original": {
                            "url": expected_original_uri
                        },
                        "timegate": {
                            "url": expected_urig
                        }
                    }
                ),
            redirurim: 
                mock_response(
                    headers = {
                        'content-type': 'text/html',
                        'memento-datetime': "Sat, 02 Feb 2008 06:29:13 GMT",
                        'link': """<{}>; rel="original", 
                            <{}>; rel="timegate",
                            <http://myarchive.org/timemap/http://example.com/something>; rel="timemap",
                            <{}>; rel="memento"
                            """.format(redir_expected_original_uri, redir_expected_urig, urim)
                    },
                    text = expected_content,
                    content = expected_content,
                    status = 200,
                    url = redirurim,
                    links = {
                        "original": {
                            "url": redir_expected_original_uri
                        },
                        "timegate": {
                            "url": redir_expected_urig
                        }
                    }
                ),
            redirurim_raw: 
                mock_response(
                    headers = {
                        'content-type': 'text/html',
                    },
                    text = expected_raw_content,
                    content = expected_raw_content,
                    status = 200,
                    url = redirurim_raw
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
        self.assertEqual(mr.timegate, redir_expected_urig)
        self.assertEqual(mr.original_uri, redir_expected_original_uri)
        self.assertEqual(mr.content, expected_content)
        self.assertEqual(mr.raw_content, expected_raw_content)

    def test_permacc_hashstyle_uris(self):

        urim = "http://perma.cc/RZP7-3P4P"
        expected_original_uri = "http://www.environment.gov.au/minister/hunt/2014/mr20141215a.html"
        expected_urim = "https://perma-archives.org/warc/20151028031045/http://www.environment.gov.au/minister/hunt/2014/mr20141215a.html"
        expected_raw_uri = "https://perma-archives.org/warc/20151028031045id_/http://www.environment.gov.au/minister/hunt/2014/mr20141215a.html"
        expected_urig = "https://perma-archives.org/warc/timegate/http://www.environment.gov.au/minister/hunt/2014/mr20141215a.html"

        expected_content = "hi"
        expected_raw_content = "hi there"

        cachedict = {
            urim:
                mock_response(
                    headers = {
                        'content-type': 'text/html',
                        'memento-datetime': "Sat, 02 Feb 2008 06:29:13 GMT",
                        'link': """<{}>; rel="original", 
                            <{}>; rel="timegate",
                            <http://myarchive.org/timemap/http://example.com/something>; rel="timemap",
                            <{}>; rel="memento"
                            """.format(expected_original_uri, expected_urig, urim)
                    },
                    text = expected_content,
                    status=200,
                    url = urim,
                    links = {
                        "original": {
                            "url": expected_original_uri
                        },
                        "timegate": {
                            "url": expected_urig
                        }
                    }
                ),
            expected_raw_uri:
                mock_response(
                    headers = {
                        'content-type': 'text/html',
                        'memento-datetime': "Sat, 02 Feb 2008 06:29:13 GMT",
                        'link': """<{}>; rel="original", 
                            <{}>; rel="timegate",
                            <http://myarchive.org/timemap/http://example.com/something>; rel="timemap",
                            <{}>; rel="memento"
                            """.format(expected_original_uri, expected_urig, expected_urim)
                    },
                    text = expected_raw_content,
                    status = 200,
                    url = expected_raw_uri,
                    links = {
                        "original": {
                            "url": expected_original_uri
                        },
                        "timegate": {
                            "url": expected_urig
                        }
                    }
                ),
            expected_urig: # requests follows all redirects, so we present the result at the end of the chain
                mock_response(
                    headers = { 
                        'content-type': 'text/html',
                        'memento-datetime': "Sat, 02 Feb 2008 06:29:13 GMT",
                        'link': """<{}>; rel="original", 
                            <{}>; rel="timegate",
                            <http://myarchive.org/timemap/http://example.com/something>; rel="timemap",
                            <{}>; rel="memento"
                            """.format(expected_original_uri, expected_urig, expected_urim)
                     },
                    text = expected_content,
                    status = 200, # after following redirects
                    url = expected_urim,
                    links = {
                        "original": {
                            "url": expected_original_uri
                        },
                        "timegate": {
                            "url": expected_urig
                        }
                    }
                ),
            expected_urim:
                mock_response(
                    headers = { 
                        'content-type': 'text/html',
                        'memento-datetime': "Sat, 02 Feb 2008 06:29:13 GMT",
                        'link': """<{}>; rel="original", 
                            <{}>; rel="timegate",
                            <http://myarchive.org/timemap/http://example.com/something>; rel="timemap",
                            <{}>; rel="memento"
                            """.format(expected_original_uri, expected_urig, expected_urim)
                     },
                    text = expected_content,
                    status = 200, # after following redirects
                    url = expected_urim,
                    links = {
                        "original": {
                            "url": expected_original_uri
                        },
                        "timegate": {
                            "url": expected_urig
                        }
                    }
                )
        }

        mh = mock_httpcache(cachedict)

        mr = memento_resource_factory(urim, mh)

        expected_mdt = datetime.strptime(
            "Sat, 02 Feb 2008 06:29:13 GMT", 
            "%a, %d %b %Y %H:%M:%S GMT"
        )

        self.maxDiff = None

        self.assertEqual(type(mr), WaybackMemento)

        self.assertEqual(mr.memento_datetime, expected_mdt)
        self.assertEqual(mr.timegate, expected_urig)
        self.assertEqual(mr.original_uri, expected_original_uri)
        self.assertEqual(mr.content, expected_content)
        self.assertEqual(mr.raw_content, expected_raw_content)

#     def test_waybackframesets(self):

#         # TODO: rework this test so that it passes
#         self.skipTest("Integration tests work, but this unit test does not produce the correct behavior")

#         urim = "http://myarchive.org/memento/20080202062913/http://example.com/something"
#         urir = "http://example.com/something"
#         raw_urim = "http://myarchive.org/memento/20080202062913id_/http://example.com/something"
#         expected_urig = "http://myarchive.org/timegate/http://example.com/something"
#         expected_original_uri = "http://example.com/something"

#         content = """
#         <html>
#             <head>
#                 <title>Is this a good title?</title>
#             </head>
#                 <!-- ARCHIVE SPECIFIC STUFF -->
#                 <frameset rows="*" cols="130,*" framespacing="0" border="0">
#                     <frame src="frame1.htm">
#                     <frame src="pages/frame2.htm">
#                     <frame src="/content/frame3.htm">
#                     <frame src="http://example2.com/content/frame4.htm">
#                 </frameset>
#         </html>"""

#         raw_content = """
#         <html>
#             <head>
#                 <title>Is this a good title?</title>
#             </head>
#                 <frameset rows="*" cols="130,*" framespacing="0" border="0">
#                     <frame src="frame1.htm">
#                     <frame src="pages/frame2.htm">
#                     <frame src="/content/frame3.htm">
#                     <frame src="http://example2.com/content/frame4.htm">
#                 </frameset>
#         </html>"""

#         timegate_stem = "http://myarchive.org/timegate/"
#         memento_stem = "http://myarchive.org/memento/"

#         cachedict = {
#             urim:
#                 mock_response(
#                     headers = {
#                         'content-type': 'text/html',
#                         'memento-datetime': "Sat, 02 Feb 2008 06:29:13 GMT",
#                         'link': """<{}>; rel="original", 
#                             <{}>; rel="timegate",
#                             <http://myarchive.org/timemap/http://example.com/something>; rel="timemap",
#                             <{}>; rel="memento"
#                             """.format(expected_original_uri, expected_urig, urim)
#                     },
#                     text = content,
#                     status=200
#                 ),
#             raw_urim:
#                 mock_response(
#                     headers = {
#                         'content-type': 'text/html'
#                     },
#                     text = raw_content,
#                     status=200
#                 ),
#             "{}/{}".format(memento_stem, urljoin(urir, "frame1.htm")):
#                 mock_response(
#                     headers = {
#                         'content-type': 'text/html'
#                     },
#                     text = "<html><body><p>frame1</p></body></html>",
#                     status=200
#                 ),
#             "{}{}".format(timegate_stem, urljoin(urir, "frame1.htm")):
#                 mock_response(
#                     headers = { 'location':  "{}/{}".format(memento_stem, urljoin(urir, "frame1.htm")) },
#                     text = "",
#                     status=302
#                 ),
#             "{}{}".format(memento_stem, urljoin(urir, "pages/frame2.htm")):
#                 mock_response(
#                     headers = {},
#                     text = "<html><body><div>frame2</div></body></html>",
#                     status=200
#                 ),
#             "{}{}".format(timegate_stem, urljoin(urir, "pages/frame2.htm")):
#                 mock_response(
#                     headers = { 'location':  "{}{}".format(memento_stem, urljoin(urir, "pages/frame2.htm")) },
#                     text = "",
#                     status=302
#                 ),
#             "{}{}".format(memento_stem, urljoin(urir, "/content/frame3.htm")):
#                 mock_response(
#                     headers = {},
#                     text = "<html><body><span><p>frame3</p></span></body></html>",
#                     status=200
#                 ),
#             "{}{}".format(timegate_stem, urljoin(urir, "/content/frame3.htm")):
#                 mock_response(
#                     headers = { 'location': "{}{}".format(memento_stem, urljoin(urir, "/content/frame3.htm")) },
#                     text = "",
#                     status=302
#                 ),
#             "http://myarchive.org/memento/20080202062913/http://example2.com/content/frame4.htm":
#                 mock_response(
#                     headers = {},
#                     text = "<html><body><div><span><p>frame4</p></span></div></body></html>",
#                     status=200
#                 ),
#             "{}{}".format(timegate_stem, "http://example2.com/content/frame4.htm"):
#                 mock_response(
#                     headers = { 'location': "http://myarchive.org/memento/20080202062913/http://example2.com/content/frame4.htm" },
#                     text = "",
#                     status=302
#                 )

#         }

#         expected_raw_content = """<html><head><title>Is this a good title?</title></head><body>
# <p>frame1</p>
# <div>frame2</div>
# <span><p>frame3</p></span>
# <div><span><p>frame4</p></span></div>
# </body></html>"""

#         expected_content = expected_raw_content

#         mh = mock_httpcache(cachedict)

#         mr = memento_resource_factory(urim, mh)

#         expected_mdt = datetime.strptime(
#             "Sat, 02 Feb 2008 06:29:13 GMT", 
#             "%a, %d %b %Y %H:%M:%S GMT"
#         )

#         self.maxDiff = None

#         self.assertEqual(type(mr), WaybackMemento)

#         self.assertEqual(mr.memento_datetime, expected_mdt)
#         self.assertEqual(mr.timegate, expected_urig)
#         self.assertEqual(mr.original_uri, expected_original_uri)
#         self.assertEqual(mr.content, expected_content)
#         self.assertEqual(mr.raw_content, expected_raw_content)
