import unittest

from datetime import datetime

from mementoembed.favicon import favicon_resource_test, \
    get_favicon_from_html, get_favicon_from_google_service, \
    construct_conventional_favicon_uri, \
    find_conventional_favicon_on_live_web, \
    query_timegate_for_favicon, \
    get_favicon_from_resource_content

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

    def get(self, uri, **args):
        return self.cachedict[uri]

class TestFavicon(unittest.TestCase):

    def test_construct_conventional_favicon_uri(self):

        scheme = "http"
        domain = "example.com"

        expecteduri = "{}://{}/favicon.ico".format(scheme, domain)

        self.assertEqual(construct_conventional_favicon_uri(scheme, domain), expecteduri)

    def test_favicon_resource_test(self):

        headers = {
            'content-type': 'image/testing'
        }

        # happy path - all is as expected
        mr = mock_response(headers=headers, status=200, content="a", url="testing-url://notused")

        self.assertEqual(favicon_resource_test(mr), True)

        # empty content
        mr = mock_response(headers=headers, status=200, content="", url="testing-url://notused")

        self.assertEqual(favicon_resource_test(mr), False)

        # 404 not found for favicon
        mr = mock_response(headers=headers, status=404, content="a", url="testing-url://notused")

        self.assertEqual(favicon_resource_test(mr), False)

        # favicon has no content-type
        mr = mock_response(headers={}, status=200, content="a", url="testing-url://notused")

        self.assertEqual(favicon_resource_test(mr), False)

    def test_get_favicon_from_html_rel_icon(self):

        expected_favicon = "http://myarchive.org/content/favicon.ico"

        content="""<html>
        <head>
            <title>Is this a good title?</title>
            <link rel="icon" href="{}">
        </head>
        <body>Is this all there is to content?</body>
        </html>""".format(expected_favicon)

        self.assertEqual(get_favicon_from_html(content), expected_favicon)

    def test_get_favicon_from_html_rel_shortcut(self):

        expected_favicon = "http://myarchive.org/content/favicon.ico"

        content="""<html>
        <head>
            <title>Is this a good title?</title>
            <link rel="shortcut" href="{}">
        </head>
        <body>Is this all there is to content?</body>
        </html>""".format(expected_favicon)

        self.assertEqual(get_favicon_from_html(content), expected_favicon)

    def test_get_favicon_from_html_rel_shortcut_icon(self):

        expected_favicon = "http://myarchive.org/content/favicon.ico"

        content="""<html>
        <head>
            <title>Is this a good title?</title>
            <link rel="shortcut icon" href="{}">
        </head>
        <body>Is this all there is to content?</body>
        </html>""".format(expected_favicon)

        self.assertEqual(get_favicon_from_html(content), expected_favicon)

    def test_get_favicon_from_google(self):

        inputuri = "http://example.com/myexample/example.html"
        expected_favicon = "https://www.google.com/s2/favicons?domain=example.com"

        cachedict = {
            inputuri: 
                mock_response(
                    headers = {},
                    content = "a",
                    status = 200,
                    url = "testing-url://notused"
                ),
            "https://www.google.com/s2/favicons?domain=example.com" :
                mock_response(
                    headers = { 'content-type': 'image/testing' },
                    content = "a",
                    status = 200,
                    url = "testing-url://notused"
                )
        }

        mh = mock_httpcache(cachedict)

        self.assertEqual(
                get_favicon_from_google_service(mh, inputuri),
                expected_favicon
        )

        inputuri = "http://example.com/myexample/example.html"

        cachedict = {
            inputuri: 
                mock_response(
                    headers = {},
                    content = "a",
                    status = 200,
                    url = "testing-url://notused"
                ),
            "https://www.google.com/s2/favicons?domain=example.com" :
                mock_response(
                    headers = { 'content-type': 'image/testing' },
                    content = "",
                    status = 404,
                    url = "testing-url://notused"
                )
        }

        mh = mock_httpcache(cachedict)

        self.assertEqual(
                get_favicon_from_google_service(mh, inputuri),
                None
        )

    def test_find_conventional_favicon_on_live_web(self):

        scheme = "http"
        domain = "example.com"

        expecteduri = "{}://{}/favicon.ico".format(scheme, domain)

        cachedict = {
            expecteduri: 
                mock_response(
                    headers = { 'content-type': 'image/testing' },
                    content = "a",
                    status = 200,
                    url = "testing-url://notused"
                )
        }

        mh = mock_httpcache(cachedict)

        self.assertEqual(
            find_conventional_favicon_on_live_web(scheme, domain, mh),
            expecteduri
        )

        cachedict = {
            expecteduri: 
                mock_response(
                    headers = { 'content-type': 'image/testing' },
                    content = "a",
                    status = 404,
                    url = "testing-url://notused"
                )
        }

        mh = mock_httpcache(cachedict)

        self.assertEqual(
            find_conventional_favicon_on_live_web(scheme, domain, mh),
            None
        )

    def test_query_timegate_for_favicon(self):

        scheme = "http"
        domain = "example.com"

        timegate_stem = "http://example-archive.org/timegate/"
        candidate_favicon_uri = "{}://{}/favicon.ico".format(scheme, domain)
        accept_datetime = datetime(2018, 1, 1, 0, 0, 0)

        urim = "http://example-archive.org/memento/{}".format(candidate_favicon_uri)

        cachedict = {
            "{}{}".format(timegate_stem, candidate_favicon_uri):
                mock_response(
                    headers = { 'location': urim },
                    content = "",
                    status = 200,
                    url = urim
                ),
            urim:
                mock_response(
                    headers = { 'content-type': 'image/testing' },
                    content = "a",
                    status = 200,
                    url = urim
                )
        }

        mh = mock_httpcache(cachedict)

        self.assertEqual(
            query_timegate_for_favicon(timegate_stem, candidate_favicon_uri, accept_datetime, mh),
            urim
        )

        cachedict = {
            "{}{}".format(timegate_stem, candidate_favicon_uri):
                mock_response(
                    headers = { 'location': urim },
                    content = "",
                    status = 302,
                    url = "testing-url://notused"
                ),
            urim:
                mock_response(
                    headers = { 'content-type': 'image/testing' },
                    content = "a",
                    status = 404,
                    url = "testing-url://notused"
                )
        }

        mh = mock_httpcache(cachedict)

        self.assertEqual(
            query_timegate_for_favicon(timegate_stem, candidate_favicon_uri, accept_datetime, mh),
            None
        )

        cachedict = {
            "{}{}".format(timegate_stem, candidate_favicon_uri):
                mock_response(
                    headers = { 'location': urim },
                    content = "",
                    status = 302,
                    url = "testing-url://notused"
                ),
            urim:
                mock_response(
                    headers = { },
                    content = "a",
                    status = 200,
                    url = "testing-url://notused"
                )
        }

        mh = mock_httpcache(cachedict)

        self.assertEqual(
            query_timegate_for_favicon(timegate_stem, candidate_favicon_uri, accept_datetime, mh),
            None
        )

    def test_get_favicon_from_resource_content(self):

        uri = "http://myarchive.org/mydir/mypage.html"

        expected_favicon = "http://myarchive.org/content/favicon.ico"

        content="""<html>
        <head>
            <title>Is this a good title?</title>
            <link rel="shortcut" href="{}">
        </head>
        <body>Is this all there is to content?</body>
        </html>""".format(expected_favicon)

        cachedict = {
            uri:
                mock_response(
                    headers = { },
                    content = content,
                    status = 200,
                    url = "testing-url://notused"
                ),
            expected_favicon:
                mock_response(
                    headers = { 'content-type': 'image/testing' },
                    content = "a",
                    status = 200,
                    url = "testing-url://notused"
                )
        }

        mh = mock_httpcache(cachedict)

        self.assertEqual(
            get_favicon_from_resource_content(uri, mh),
            expected_favicon
        )

        