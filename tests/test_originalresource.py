import unittest

from mementoembed.mementoresource import memento_resource_factory
from mementoembed.originalresource import OriginalResource

class mock_response:

    def __init__(self, headers, text, status, url, content=None, links={}):
        self.headers = headers
        self.text = text
        if content is None:
            self.content = bytes(text.encode('utf-8'))
        else:
            self.content = content

        self.status_code = status
        self.url = url

        self.links = links

class mock_httpcache:
    """
        rather than hitting the actual HTTP cache,
        we can simulate behavior for this test
    """

    def __init__(self, cachedict):
        self.cachedict = cachedict

    def get(self, uri, headers=None):
        return self.cachedict[uri]

    def close(self):
        pass


class TestOriginalResource(unittest.TestCase):

    def test_simplecase_rotten_resource(self):

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
            expected_urig:
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
            expected_original_uri:
                mock_response(
                    headers = {},
                    text = "",
                    status=404,
                    url = expected_original_uri
                )
        }

        mh = mock_httpcache(cachedict)

        mr = memento_resource_factory(urim, mh)

        ores = OriginalResource(mr, mh)

        self.assertEqual(ores.domain, "example.com")
        self.assertEqual(ores.uri, "http://example.com/something")
        self.assertEqual(ores.link_status, "Rotten")

    def test_simplecase_live_resource(self):

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
            expected_urig:
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
            expected_original_uri:
                mock_response(
                    headers = {
                        'content-type': 'text/html'
                    },
                    text = "",
                    status=200,
                    url = expected_original_uri
                )
        }

        mh = mock_httpcache(cachedict)

        mr = memento_resource_factory(urim, mh)

        ores = OriginalResource(mr, mh)

        self.assertEqual(ores.domain, "example.com")
        self.assertEqual(ores.uri, "http://example.com/something")
        self.assertEqual(ores.link_status, "Live")

    def test_favicon_from_html(self):

        urim = "http://myarchive.org/memento/http://example.com/something"
        expected_urig = "http://myarchive.org/timegate/http://example.com/something"
        expected_original_uri = "http://example.com/something"
        expected_favicon = "http://myarchive.org/memento/http://example.com/content/favicon.ico"
        original_favicon = "http://example.com/content/favicon.ico"
        favicon_urig = "http://myarchive.org/timegate/http://example.com/favicon.ico"

        expected_content = """
        <html>
            <head>
                <title>Is this a good title?</title>
                <link rel="icon" href="{}" >
            </head>
            <body>
                Is this good text?
            </body>
        </html>""".format(original_favicon)

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
            expected_urig:
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
            original_favicon:
                mock_response(
                    headers = {
                        'content-type': 'image/',
                    },
                    text = expected_content,
                    status=200,
                    url = expected_favicon
                ),
            expected_original_uri:
                mock_response(
                    headers = {
                        'content-type': 'text/html',
                    },
                    text = "",
                    status=200,
                    url = expected_original_uri
                ),
            "http://myarchive.org/timegate/http://example.com/content/favicon.ico":
                mock_response(
                    headers = {"location": expected_favicon},
                    text = "",
                    status = 200,
                    url = expected_favicon
                ),
            favicon_urig:
                mock_response(
                    headers = {'content-type': 'image/'},
                    text = "a",
                    status=200,
                    url = expected_favicon
                ),
            expected_favicon:
                mock_response(
                    headers = {'content-type': 'image/'},
                    text = "a",
                    status=200,
                    url = expected_favicon
                )

        }

        mh = mock_httpcache(cachedict)

        mr = memento_resource_factory(urim, mh)

        ores = OriginalResource(mr, mh)

        self.assertEqual(ores.domain, "example.com")
        self.assertEqual(ores.uri, "http://example.com/something")
        self.assertEqual(ores.link_status, "Live")
        self.assertEqual(ores.favicon, expected_favicon)

    # TODO: test the other favicon search states
