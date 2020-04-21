import os
import unittest

from mementoembed.imageselection import get_image_list, score_image, get_best_image

class TestImageSelection(unittest.TestCase):

    def test_get_image_list(self):

        expected_imagelist = [
            "http://example.com/images/image1.test", # absolute uri, same domain
            "https://example2.com/myimage.test", # absolute uri, different domain
            "http://example.com/images/image2.test", # relative uri
            """data:image/gif;base64,R0lGODlhyAAiALMAAFONvX2pzbPN4p6/2tTi7mibxYiw0d/q86nG3r7U5l2UwZO31unx98nb6nOiyf///yH5BAUUAA8ALAAAAADIACIAAAT/8MlJq7046827/2AojmRpnmiqriwGvG/Qjklg28es73wHxz0P4gcgBI9IHVGWzAx/xqZ0KlpSLU9Y9MrtVqzeBwFBJjPCaC44zW4HD4TzZI0h2OUjON7EsMd1fXcrfnsfgYUSeoYLPwoLZ3QTDAgORAoGWxQHNzYSBAY/BQ0XNZw5mgMBRACOpxSpnLE3qKqWC64hk5WNmBebnA8MjC8KFAygMAUCErA2CZoKq6wHkQ8C0dIxhQRED8OrC1hEmQ+12QADFebnABTr0ukh1+wB20QMu0ASCdn16wgTDmCTNlDfhG/sFODi9iMLvAoOi6hj92LZhHfZ3FEEYNEDwnMK/ykwhDEATAN2C/5d3PiDiYSIrALkg6EAz0hiFDNFJKeqgIEyM1nhwShNo0+glhBhgKlA5qqaE25KY1KAYkGAYlYVSEAgQdU1DFbFe3DgKwysWcHZ+QjAAIWdFQaMgkjk2b4ySLtNkCvuh90NYYmMLUsErVRiC8o8OLmkAYF5hZkRKYCHgVmDAiJJLeZpVUdrq/DA7XB5rAV+gkn/MJ0hc8sKm6OuclDoo8tgBQFgffd335p3cykEjSK1gIXLEl+Oq9OgTIKZtymg/hHuAoHmZJ6/5gDcwvDOyysEDS7B9VkJoSsEhuEyN6KSPyxKrf4qsnIoFQ4syL0qum8i9AW0H/9F/l3gngXwwSAfEQ5csIoFUmH1oAVrTEhXQ+Cdd6GGD4z230b+TQdDgB8S6INeG76AlVSsoYeibBg+cOAX2z1g4Vv2sYggER15uFliZFwWnUAAQmhLGUKe+MMFEa1oH40/FMKYht1RMKVB7+AiwTvEMehdeB2CicwLlAlXI1m5kSjBmACUOQF0HWRpAZcZqngBbxWwqZtkZz4QlEsJvkDiejDIcRh5h4kG5pPBrEHkDw06GKMEhAJwGxx+uBIoAIOmlxaH9TWCh4h2fgqDAWcc019AqwTHwDtu1UmMRQnkdpuHRU6gZ3uWOOaHILmuScc6LlFDhKuwwgiqsjQNgAD/UWgFZaKuq/w0AHIAuHIYReR5+A4C12HkEksSfRvuqiuxR4GebSFw7SraMqoRuXvK2t+Z+JDb22bsxDqBh+YRVCO5RgT81JnEGiNtNvvKKwl/IzJKql8ORadqQuSZis7CANCWYnIScOyAiJHayFIUIpM8r0GUstsrbA4HhC2nJi9LwDuihKkuhEQpgAAiEQpjyc99aWHMppz2gSLBlCL9iFQrW2pdz0TDPCkGCRgQjU9GVPpZQAkgIICWHfQhABkNkM1svQxg9wcJfWSn1AlxI5DA3COYjbbaLJBKzhQRuiF4Cn8nMiMXgQ+uOAkBFDDA2wxABkPJiMe8+OUaECVNLMZUJI755xtoHmwXnoNuugUQp4bGLzf0dvrriy2wsAMD4A377YJjSgDfD0QAADs="""
        ]

        htmlcontent = """<html>
        <head>
            <title>Is this a good title?</title>
        </head>
        <body>
            <p>some text</p>
            <img src="{}">
            <img src="{}">
            <img src="/images/image2.test">
            <img src="{}">
        </body>
        </html>""".format(
            expected_imagelist[0], expected_imagelist[1],
            expected_imagelist[3]
            )

        class mock_httpcache:

            def get(self, uri):
                return mock_Response()

        class mock_Response:

            @property
            def text(self):
                return htmlcontent

        mh = mock_httpcache()
        uri = "http://example.com/example.html"

        self.assertEqual(
            get_image_list(uri, mh),
            expected_imagelist
        )

    def test_score_image(self):

        imagedata = [
            "NYT_home_banner.gif",
            "dis_PAGEONE_75.jpg",
            "go_button.gif",
            "jobs.gif",
            "line2gray5x468.gif",
            "mm_1b.gif",
            "mostemailed.gif",
            "onthisday.gif",
            "p_videopageone.gif",
            "serbia.184.1.jpg",
            "sfu-160x105.jpg",
            "spacer.gif"
            ]

        imagedir = "{}/samples/images".format(
            os.path.dirname(os.path.realpath(__file__)
            ))

        #print()

        maxscore = None

        for imagefile in imagedata:
            with open("{}/{}".format(imagedir, imagefile), 'rb') as f:
                imagedata = f.read()

            score = score_image(imagedata, 0, 0)

            if maxscore is None:
                maxscore = score
            else:
                if score > maxscore:
                    maxscore = score
                    max_score_image = imagefile

            #print("{}: {}".format(imagefile, score))

        self.assertEqual(max_score_image, "serbia.184.1.jpg")

    def test_best_image(self):
        expected_imagelist = [
            "http://example.com/images/image1.test", # absolute uri, same domain
            "https://example2.com/myimage.test", # absolute uri, different domain
            "http://example.com/images/image2.test", # relative uri
            """data:image/gif;base64,R0lGODlhyAAiALMAAFONvX2pzbPN4p6/2tTi7mibxYiw0d/q86nG3r7U5l2UwZO31unx98nb6nOiyf///yH5BAUUAA8ALAAAAADIACIAAAT/8MlJq7046827/2AojmRpnmiqriwGvG/Qjklg28es73wHxz0P4gcgBI9IHVGWzAx/xqZ0KlpSLU9Y9MrtVqzeBwFBJjPCaC44zW4HD4TzZI0h2OUjON7EsMd1fXcrfnsfgYUSeoYLPwoLZ3QTDAgORAoGWxQHNzYSBAY/BQ0XNZw5mgMBRACOpxSpnLE3qKqWC64hk5WNmBebnA8MjC8KFAygMAUCErA2CZoKq6wHkQ8C0dIxhQRED8OrC1hEmQ+12QADFebnABTr0ukh1+wB20QMu0ASCdn16wgTDmCTNlDfhG/sFODi9iMLvAoOi6hj92LZhHfZ3FEEYNEDwnMK/ykwhDEATAN2C/5d3PiDiYSIrALkg6EAz0hiFDNFJKeqgIEyM1nhwShNo0+glhBhgKlA5qqaE25KY1KAYkGAYlYVSEAgQdU1DFbFe3DgKwysWcHZ+QjAAIWdFQaMgkjk2b4ySLtNkCvuh90NYYmMLUsErVRiC8o8OLmkAYF5hZkRKYCHgVmDAiJJLeZpVUdrq/DA7XB5rAV+gkn/MJ0hc8sKm6OuclDoo8tgBQFgffd335p3cykEjSK1gIXLEl+Oq9OgTIKZtymg/hHuAoHmZJ6/5gDcwvDOyysEDS7B9VkJoSsEhuEyN6KSPyxKrf4qsnIoFQ4syL0qum8i9AW0H/9F/l3gngXwwSAfEQ5csIoFUmH1oAVrTEhXQ+Cdd6GGD4z230b+TQdDgB8S6INeG76AlVSsoYeibBg+cOAX2z1g4Vv2sYggER15uFliZFwWnUAAQmhLGUKe+MMFEa1oH40/FMKYht1RMKVB7+AiwTvEMehdeB2CicwLlAlXI1m5kSjBmACUOQF0HWRpAZcZqngBbxWwqZtkZz4QlEsJvkDiejDIcRh5h4kG5pPBrEHkDw06GKMEhAJwGxx+uBIoAIOmlxaH9TWCh4h2fgqDAWcc019AqwTHwDtu1UmMRQnkdpuHRU6gZ3uWOOaHILmuScc6LlFDhKuwwgiqsjQNgAD/UWgFZaKuq/w0AHIAuHIYReR5+A4C12HkEksSfRvuqiuxR4GebSFw7SraMqoRuXvK2t+Z+JDb22bsxDqBh+YRVCO5RgT81JnEGiNtNvvKKwl/IzJKql8ORadqQuSZis7CANCWYnIScOyAiJHayFIUIpM8r0GUstsrbA4HhC2nJi9LwDuihKkuhEQpgAAiEQpjyc99aWHMppz2gSLBlCL9iFQrW2pdz0TDPCkGCRgQjU9GVPpZQAkgIICWHfQhABkNkM1svQxg9wcJfWSn1AlxI5DA3COYjbbaLJBKzhQRuiF4Cn8nMiMXgQ+uOAkBFDDA2wxABkPJiMe8+OUaECVNLMZUJI755xtoHmwXnoNuugUQp4bGLzf0dvrriy2wsAMD4A377YJjSgDfD0QAADs="""
        ]

        htmlcontent = """<html>
        <head>
            <title>Is this a good title?</title>
        </head>
        <body>
            <p>some text</p>
            <img src="{}">
            <img src="{}">
            <img src="/images/image2.test">
            <img src="{}">
        </body>
        </html>""".format(
            expected_imagelist[0], expected_imagelist[1],
            expected_imagelist[3]
            )

        class mock_Response:

            def __init__(self, content, headers):
                self.content = content
                self.headersdict = headers
                self.status_code = 200

            @property
            def text(self):
                return self.content

            @property
            def headers(self):
                return self.headersdict

        class mock_httpcache:

            def __init__(self):

                self.uri_to_content = {}
                self.uri_to_headers = {}
                self.timeout = 15

                imagedir = "{}/samples/images".format(
                    os.path.dirname(os.path.realpath(__file__))
                )

                with open("{}/spacer.gif".format(imagedir), 'rb') as f:
                    data = f.read()
                    uri = "http://example.com/images/image1.test"
                    self.uri_to_content[uri] = data
                    self.uri_to_headers[uri] = {'content-type': 'image/testing', 'memento-datetime': 'cheese'}

                with open("{}/mm_1b.gif".format(imagedir), 'rb') as f:
                    data = f.read()
                    uri = "https://example2.com/myimage.test"
                    self.uri_to_content[uri] = data
                    self.uri_to_headers[uri] = {'content-type': 'image/testing', 'memento-datetime': 'cheese'}

                with open("{}/serbia.184.1.jpg".format(imagedir), 'rb') as f:
                    data = f.read()
                    uri = "http://example.com/images/image2.test"
                    self.uri_to_content[uri] = data
                    self.uri_to_headers[uri] = {'content-type': 'image/testing', 'memento-datetime': 'cheese'}

                uri = "http://example.com/example.html"
                self.uri_to_content[uri] = htmlcontent
                self.uri_to_headers[uri] = {'content-type': 'text/html'}

            def get(self, uri):
                return mock_Response(
                    self.uri_to_content[uri],
                    self.uri_to_headers[uri]
                    )

        class mock_future:

            def __init__(self, uri, httpcache):
                self.uri = uri
                self.httpcache = httpcache

            def done(self):
                return True

            def result(self):
                return self.httpcache.get(self.uri)

            def cancel(self):
                pass

        class mock_futuressession:

            def __init__(self, httpcache):
                self.httpcache = httpcache

            def get(self, uri):
                return mock_future(uri, self.httpcache)

        mh = mock_httpcache()
        uri = "http://example.com/example.html"

        self.assertEqual(
            get_best_image(uri, mh, futuressession=mock_futuressession(mh)),
            "http://example.com/images/image2.test"
            )

