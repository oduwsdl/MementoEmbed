import os
import unittest

from mementoembed import Surrogate

class TestSurrogate(unittest.TestCase):

    testdir = os.path.dirname(os.path.realpath(__file__))

    def test_surrogate1(self):

        with open("{}/samples/fivethirtyeight.com.html".format(self.testdir), encoding='utf8') as f:
            content = f.read()

        expected_snippet = "Nate Silver’s FiveThirtyEight uses statistical analysis — hard numbers — to tell compelling stories about elections, politics, sports, science, economics and lifestyle."

        s = Surrogate("http://fivethirtyeight.com", content, {'header1': 'value1'})

        self.assertEqual(s._getMetadataDescription(), expected_snippet)

        og_snippet = "Nate Silver’s FiveThirtyEight uses statistical analysis — hard numbers — to tell compelling stories about elections, politics, sports, science, economics and lifestyle."

        self.assertEqual(s._getMetadataOGDescription(), og_snippet)        

        self.assertEqual(s.text_snippet, expected_snippet)

        expected_title = "FiveThirtyEight | Nate Silver’s FiveThirtyEight uses statistical analysis — hard numbers — to tell compelling stories about politics, sports, science, economics and culture."

        self.assertEqual(s.title, expected_title)

        expected_image_uri = "https://s0.wp.com/i/blank.jpg"

        self.assertEqual(s.striking_image, expected_image_uri)

    def test_surrogate2(self):

        with open("{}/samples/shawnmjones.org.html".format(self.testdir), encoding='utf8') as f:
            content = f.read()

        expected_snippet = "Description of the professional life of Shawn M. Jones"

        s = Surrogate("http://www.shawnmjones.org", content, {'header1': 'value1'})

        twitter_snippet = "Everything you need to know about Shawn M. Jones"

        self.assertEqual(s._getMetadataTwitterDescription(), twitter_snippet)

        og_snippet = "Description of the professional life of Shawn M. Jones"

        self.assertEqual(s._getMetadataOGDescription(), og_snippet)

        self.assertEqual(s.text_snippet, expected_snippet)

        expected_title = "Shawn M. Jones"

        self.assertEqual(s.title, expected_title)

        expected_image_uri = "http://www.shawnmjones.org/images/20_me.jpg"

        self.assertEqual(s.striking_image, expected_image_uri)

    def test_surrogate3(self):

        with open("{}/samples/odu.edu_compsci.html".format(self.testdir), encoding='utf8') as f:
            content = f.read()

        expected_snippet = "Featured Faculty: Cong Wang Cong Wang received his PhD at Stony Brook University, where he worked on mobile computing, algorithm and optimization. His research interests lie in mobile computing, cybersecurity, machine learning and energy-efficiency. Prior joining ODU, he worked at Huawei U.S. Res..."

        s = Surrogate("http://www.odu.edu/compsci", content, {'header1': 'value1'})

        twitter_snippet = None

        self.assertEqual(s._getMetadataTwitterDescription(), twitter_snippet)

        og_snippet = ""

        self.assertEqual(s._getMetadataOGDescription(), og_snippet)

        self.assertEqual(s.text_snippet, expected_snippet)

        expected_title = "Department of Computer Science - Old Dominion University"

        self.assertEqual(s.title, expected_title)

        expected_image_uri = "https://web.archive.org/web/20171205043718im_/http://www.odu.edu/compsci/_jcr_content/image.img.1280.jpg"

        self.assertEqual(s.striking_image, expected_image_uri)
