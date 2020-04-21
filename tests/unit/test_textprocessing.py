import unittest

from mementoembed.textprocessing import extract_text_snippet, extract_title

class TestTextProcessing(unittest.TestCase):

    def test_title_simplecase(self):

        expectedtitle = "Is this a good title?"

        htmlcontent = "<html><head><title>{}</title></head><body>This is some body text.</body></html>".format(expectedtitle)

        self.assertEqual(extract_title(htmlcontent), expectedtitle)

    def test_title_multiline(self):

        expectedtitle = "Is this a good title?"
        multilinetitle = expectedtitle.replace(' ', '\n')

        htmlcontent = "<html><head><title>{}</title></head><body>This is some body text.</body></html>".format(multilinetitle)

        self.assertEqual(extract_title(htmlcontent), expectedtitle)

    def test_title_multispace(self):

        expectedtitle = "Is this a good title?"
        multispacetitle = "Is    this a  good    title?    "

        htmlcontent = "<html><head><title>{}</title></head><body>This is some body text.</body></html>".format(multispacetitle)

        self.assertEqual(extract_title(htmlcontent), expectedtitle)

    def test_title_twitter_metatag(self):

        expectedtitle = "Is this a good title?"

        htmlcontent = """<html>
        <head>
            <title>notatitle</title>
            <meta name="twitter:title" content="{}">
        </head>
        <body>This is some body text.</body>
        </html>""".format(expectedtitle)

        self.assertEqual(extract_title(htmlcontent), expectedtitle)

    def test_title_ogp_metatag(self):

        expectedtitle = "Is this a good title?"

        htmlcontent = """<html>
        <head>
            <title>notatitle</title>
            <meta property="og:title" content="{}">
        </head>
        <body>This is some body text.</body>
        </html>""".format(expectedtitle)

        self.assertEqual(extract_title(htmlcontent), expectedtitle)

    def test_title_misused_ogp_metatag(self):
        """
            The documentation states that ogp fields should be used with the
            property attribute of the meta tag. What if they use name instead?
        """

        expectedtitle = "Is this a good title?"

        htmlcontent = """<html>
        <head>
            <title>notatitle</title>
            <meta name="og:title" content="{}">
        </head>
        <body>This is some body text.</body>
        </html>""".format(expectedtitle)

        self.assertEqual(extract_title(htmlcontent), expectedtitle)


    def test_title_misused_twitter_metatag(self):
        """
            The documentation states that ogp fields should be used with the
            property attribute of the meta tag. What if they use name instead?
        """

        expectedtitle = "Is this a good title?"

        htmlcontent = """<html>
        <head>
            <title>notatitle</title>
            <meta name="twitter:title" content="{}">
        </head>
        <body>This is some body text.</body>
        </html>""".format(expectedtitle)

        self.assertEqual(extract_title(htmlcontent), expectedtitle)

    def test_title_property_preference(self):
        """
            The system should prefer OGP over Twitter over title tag.
        """

        expectedtitle = "Is this a good title?"

        htmlcontent = """<html>
        <head>
            <title>notatitle</title>
            <meta name="twitter:title" content="not a title">
            <meta name="og:title" content="{}">
        </head>
        <body>This is some body text.</body>
        </html>""".format(expectedtitle)

        self.assertEqual(extract_title(htmlcontent), expectedtitle)

    def test_title_garbage_input(self):

        garbage = b'<html></html>r\x8d\xe0\x95z\xc5\xf1'

        self.assertEqual(extract_title(garbage), "")

    def test_snippet_twitter(self):

        expectedsnippet = "This is some body text."

        htmlcontent = """<html>
        <head>
            <title>My Title</title>
            <meta name="twitter:description" content="{}">
        </head>
        <body>not a description</body>
        </html>".format(expectedsnippet)
        """.format(expectedsnippet)

        self.assertEqual(extract_text_snippet(htmlcontent), expectedsnippet)

    def test_snippet_ogp(self):

        expectedsnippet = "This is a snippet."

        htmlcontent = """<html>
        <head>
            <title>My Title</title>
            <meta name="og:description" content="{}">
        </head>
        <body>not a description</body>
        </html>".format(expectedsnippet)
        """.format(expectedsnippet)

        self.assertEqual(extract_text_snippet(htmlcontent), expectedsnippet)

    def test_snippet_preference(self):
        """
            The system should prefer OGP over Twitter over title tag.
        """

        expectedsnippet = "This is a snippet."

        htmlcontent = """<html>
        <head>
            <title>notatitle</title>
            <meta name="twitter:description" content="not a snippet">
            <meta name="og:description" content="{}">
        </head>
        <body>not a description</body>
        </html>""".format(expectedsnippet)

        self.assertEqual(extract_text_snippet(htmlcontent), expectedsnippet)

    def test_snippet_nometa(self):
        """
            We fall back to other methods if no snippet.
        """

        expectedsnippet = "This is a snippet."

        htmlcontent = """<html>
        <head>
            <title>notatitle</title>
        </head>
        <body>{}</body>
        </html>""".format(expectedsnippet)

        self.assertEqual(extract_text_snippet(htmlcontent), expectedsnippet)

    def test_snippet_nocontent(self):
        """
            We deliver an empty snippet if no metadata and no content.
        """

        expectedsnippet = ""

        htmlcontent = """<html>
        <head>
            <title>notatitle</title>
        </head>
        <body><object src="some_flash_stuff"></object></body>
        </html>"""

        self.assertEqual(extract_text_snippet(htmlcontent), expectedsnippet)

    def test_snippet_toolong(self):

        reallylongstring = "a" * 200
        expectedsnippet = reallylongstring[0:197] + '...'

        htmlcontent = """<html>
        <head>
            <title>notatitle</title>
        </head>
        <body>{}</body>
        </html>""".format(reallylongstring)

        self.assertEqual(extract_text_snippet(htmlcontent), expectedsnippet)


    def test_snippet_empty_twitter_metatag(self):

        reallylongstring = "a" * 200
        expectedsnippet = reallylongstring[0:197] + '...'

        htmlcontent = """<html>
        <head>
            <title>notatitle</title>
            <meta name="twitter:description" content="">
        </head>
        <body>{}</body>
        </html>""".format(reallylongstring)

        self.assertEqual(extract_text_snippet(htmlcontent), expectedsnippet)


    def test_snippet_empty_ogp_metatag(self):

        reallylongstring = "a" * 200
        expectedsnippet = reallylongstring[0:197] + '...'

        htmlcontent = """<html>
        <head>
            <title>notatitle</title>
            <meta name="og:description" content="">
        </head>
        <body>{}</body>
        </html>""".format(reallylongstring)

        self.assertEqual(extract_text_snippet(htmlcontent), expectedsnippet)






