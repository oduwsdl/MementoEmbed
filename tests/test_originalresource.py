import unittest

from mementoembed.mementoresource import memento_resource_factory
from mementoembed.originalresource import OriginalResource

class mock_response:

    def __init__(self, headers, text, status, content=None):
        self.headers = headers
        self.text = text
        if content is None:
            self.content = bytes(text.encode('utf-8'))
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
                        'memento-datetime': "Fri, 22 Jun 2018 21:16:36 GMT",
                        'link': """<{}>; rel="original", 
                            <{}>; rel="timegate",
                            <http://myarchive.org/timemap/http://example.com/something>; rel="timemap",
                            <{}>; rel="memento"
                            """.format(expected_original_uri, expected_urig, urim)
                    },
                    text = expected_content,
                    status=200
                ),
            expected_original_uri:
                mock_response(
                    headers = {},
                    text = "",
                    status=404
                )
        }

        mh = mock_httpcache(cachedict)

        mr = memento_resource_factory(urim, mh)

        ores = OriginalResource(mr, mh)

        self.assertEquals(ores.domain, "example.com")
        self.assertEquals(ores.uri, "http://example.com/something")
        self.assertEquals(ores.link_status, "Rotten")

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
                        'memento-datetime': "Fri, 22 Jun 2018 21:16:36 GMT",
                        'link': """<{}>; rel="original", 
                            <{}>; rel="timegate",
                            <http://myarchive.org/timemap/http://example.com/something>; rel="timemap",
                            <{}>; rel="memento"
                            """.format(expected_original_uri, expected_urig, urim)
                    },
                    text = expected_content,
                    status=200
                ),
            expected_original_uri:
                mock_response(
                    headers = {},
                    text = "",
                    status=200
                )
        }

        mh = mock_httpcache(cachedict)

        mr = memento_resource_factory(urim, mh)

        ores = OriginalResource(mr, mh)

        self.assertEquals(ores.domain, "example.com")
        self.assertEquals(ores.uri, "http://example.com/something")
        self.assertEquals(ores.link_status, "Live")

    def test_favicon_from_html(self):

        urim = "http://myarchive.org/memento/http://example.com/something"
        expected_urig = "http://myarchive.org/timegate/http://example.com/something"
        expected_original_uri = "http://example.com/something"
        expected_favicon = "http://myarchive.org/memento/http://example.com/content/favicon.ico"

        expected_content = """
        <html>
            <head>
                <title>Is this a good title?</title>
                <link rel="icon" href="{}" >
            </head>
            <body>
                Is this good text?
            </body>
        </html>""".format(expected_favicon)

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
                ),
            expected_original_uri:
                mock_response(
                    headers = {},
                    text = "",
                    status=200
                ),
            expected_favicon:
                mock_response(
                    headers = {},
                    text = "",
                    status=200
                )

        }

        mh = mock_httpcache(cachedict)

        mr = memento_resource_factory(urim, mh)

        ores = OriginalResource(mr, mh)

        self.assertEquals(ores.domain, "example.com")
        self.assertEquals(ores.uri, "http://example.com/something")
        self.assertEquals(ores.link_status, "Live")
        self.assertEquals(ores.favicon, expected_favicon)

    # TODO: test the other favicon search states