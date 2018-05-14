import sys
import re
import requests

from urllib.parse import urljoin
from PIL import ImageFile
from bs4 import BeautifulSoup
from readability import Document

p = re.compile(' +')

class Surrogate:
    """
        Surrogate generates and stores all information about surrogates
        related to content, uri, and response_headers.
    """

    def __init__(self, uri, content, response_headers):

        self.uri = uri
        self.content = content
        self.response_headers = response_headers

        self.soup = BeautifulSoup(self.content, "html5lib")

        self.text_snippet_string = None
        self.striking_image_uri = None
        self.title_string = None
        self.image_list = None

    @property
    def text_snippet(self):
        if self.text_snippet_string == None or self.text_snippet_string == "":

            self.text_snippet_string = self._getMetadataDescription()

            if self.text_snippet_string == None or self.text_snippet_string == "":

                self.text_snippet_string = self._getMetadataOGDescription()

                if self.text_snippet_string == None or self.text_snippet_string == "":

                    self.text_snippet_string = self._getMetadataTwitterDescription()

                    if self.text_snippet_string == None or self.text_snippet_string == "":

                        self.text_snippet_string = self._getLede3Description()

        if len(self.text_snippet_string) > 297:
            return "{}...".format(self.text_snippet_string[0:297])
        else:
            return self.text_snippet_string

    @property
    def striking_image(self):
        
        if self.striking_image_uri == None:

            self.striking_image_uri = self._getMetadataOGImage()

            if self.striking_image_uri == None:

                self.striking_image_uri = self._getMetadataTwitterImage()

                if self.striking_image_uri == None:

                    self.striking_image_uri = self._getLargestImage()

        return self.striking_image_uri

    @property
    def title(self):

        if self.title_string == None:
            self.title_string = self.soup.title.string

        return self.title_string

    def _getMetadataDescription(self):

        description = None

        for metatag in self.soup.find_all("meta"):
            if metatag.get("name") == "description":
                description = metatag.get("content")

        return description

    def _getMetadataOGDescription(self):

        description = None

        for metatag in self.soup.find_all("meta"):
            if metatag.get("property") == "og:description":
                description = metatag.get("content")

        return description

    def _getMetadataTwitterDescription(self):

        description = None

        for metatag in self.soup.find_all("meta"):
            if metatag.get("name") == "twitter:description":
                description = metatag.get("content")

        return description
        
    def _getMetadataOGImage(self):

        imageurl = None

        for metatag in self.soup.find_all("meta"):
            if metatag.get("property") == "og:image":
                imageurl = metatag.get("content")

        return imageurl

    def _getMetadataTwitterImage(self):

        imageurl = None

        for metatag in self.soup.find_all("meta"):
            if metatag.get("name") == "twitter:image:src":
                imageurl = metatag.get("content")

        return imageurl

    def _getLede3Description(self):

        description = None

        doc = Document(self.content)

        d = doc.score_paragraphs()

        maxscore = 0
        maxpara = None

        for para in d:

            if d[para]['content_score'] > maxscore:
                maxpara = d[para]['elem']
                maxscore = d[para]['content_score']

        allparatext = maxpara.text_content().replace('\n', ' ').replace('\r', ' ').strip()
        description = p.sub(' ', allparatext)

        return description
        
    def _find_all_images(self):

        if self.image_list == None:

            self.image_list = {}

            for imgtag in self.soup.find_all("img"):

                imageuri = urljoin(self.uri, imgtag.get("src"))

                if imageuri not in self.image_list:
                    resp = requests.get(imageuri)

                    imagedata = resp.content

                    self.image_list[imageuri] = imagedata

    def _getLargestImage(self):

        maxsize = 0
        maximageuri = None

        self._find_all_images()

        for imageuri in self.image_list:

            p = ImageFile.Parser()
            p.feed(self.image_list[imageuri])

            width, height = p.image.size

            imgsize = width * height

            if imgsize > maxsize:
                maxsize = imgsize
                maximageuri = imageuri

        return maximageuri