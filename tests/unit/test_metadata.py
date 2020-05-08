import unittest
import os
import pprint

from mementoembed.pagedata import parse_page_metadata, find_metaddata_value

pp = pprint.PrettyPrinter(indent=4)

class TestMetadata(unittest.TestCase):

    def test_parse_page_metadata(self):

        sample_file = "{}/samples/htmltext.html".format(
            os.path.dirname(os.path.realpath(__file__))
        )

        with open(sample_file) as f:
            htmltext = f.read()

        metadata = parse_page_metadata(htmltext)

        pp.pprint(metadata)

        self.assertEqual(
            find_metaddata_value(metadata, 'charset'),
            'utf-8'
        )

        self.assertEqual(
            find_metaddata_value(metadata, 'property', attribute_key='og:url', attribute_value='content'),
            'https://www.shawnmjones.org/'
        )

        self.assertEqual(
            find_metaddata_value(metadata, 'property', attribute_key='og:type', attribute_value='content'),
            'website'
        )

        self.assertEqual(
            find_metaddata_value(metadata, 'property', attribute_key='og:title', attribute_value='content'),
            'Shawn M. Jones | Researcher - Software Engineer'
        )

        self.assertEqual(
            find_metaddata_value(metadata, 'property', attribute_key='og:image', attribute_value='content'),
            'https://www.shawnmjones.org/assets/images/me_outside.jpg'
        )

        self.assertEqual(
            find_metaddata_value(metadata, 'name', attribute_key='twitter:image:src', attribute_value='content'),
            'https://www.shawnmjones.org/assets/images/me_outside.jpg'
        )


if __name__ == "__main__":
    unittest.main(TestMetadata())