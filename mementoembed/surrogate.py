import sys
import re
import requests
import tldextract
import aiu

from datetime import datetime
from urllib.parse import urljoin, urlparse

from PIL import ImageFile
from bs4 import BeautifulSoup
from readability import Document
from memento_client import MementoClient

p = re.compile(' +')

class Surrogate:
    """
        Surrogate generates and stores all information about surrogates
        related to content, uri, and response_headers.
    """

    def __init__(self, uri, content, response_headers, logger=None):

        self.uri = uri
        self.content = content
        self.response_headers = response_headers

        self.soup = BeautifulSoup(self.content, "html5lib")

        self.text_snippet_string = None
        self.striking_image_uri = None
        self.title_string = None
        self.image_list = None
        self.site_favicon_uri = None
        self.logger = logger

        self.urir = None
        self.original_domainname = None
        self.original_link_status_text = None
        self.original_link_favicon_uri = None
        self.memento_dt = None

    @property
    def text_snippet(self):

        self.logger.info("selecting text snippet for {}".format(self.uri))

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
        
        self.logger.info("selecting striking image for {}".format(self.uri))

        if self.striking_image_uri == None:

            self.striking_image_uri = self._getMetadataOGImage()

            if self.striking_image_uri == None:

                self.striking_image_uri = self._getMetadataTwitterImage()

                if self.striking_image_uri == None:

                    self.striking_image_uri = self._getLargestImage()

        return self.striking_image_uri

    @property
    def title(self):

        self.logger.debug("selecting striking image for {}".format(self.uri))

        if self.title_string == None:
            self.title_string = self.soup.title.string

        return self.title_string

    @property
    def original_uri(self):

        if self.urir == None:
            self.urir = aiu.convert_LinkTimeMap_to_dict( self.response_headers['link'] )['original_uri']

        return self.urir

    @property
    def original_domain(self):

        if self.original_domainname == None:
            if self.urir == None:
                urir = self.original_uri

            o = urlparse(urir)
            original_domain = o.netloc

            self.original_domainname = original_domain

        return self.original_domainname

    @property
    def original_link_status(self):

        if self.original_link_status_text == None:

            try:
                r = requests.get(self.urir)

                if r.status_code == 200:
                    self.original_link_status_text = "Live"
                else:
                    self.original_link_status_text = "Rotten"

            except Exception:
                self.original_link_status_text = "Rotten"

        return self.original_link_status_text

    @property
    def memento_datetime(self):

        if self.memento_dt == None:
            self.memento_dt = datetime.strptime(
                self.response_headers['memento-datetime'], "%a, %d %b %Y %H:%M:%S GMT")
            
        return self.memento_dt

    @property
    def original_favicon(self):

        if self.original_link_favicon_uri == None:
            self.logger.info("interrogating HTML of memento for favicon URI")

            links = self.soup.find_all("link")

            for link in links:
                if 'icon' in link['rel']:
                    self.logger.debug("extracted favicon from HTML: {}".format(link['href']))
                    self.original_link_favicon_uri = urljoin(self.uri, link['href'])
                    break

        if self.original_link_favicon_uri == None:
            self.logger.info("querying web archive for original favicon at conventional URI")
            o = urlparse(self.original_uri)
            original_domain = o.netloc
            original_scheme = o.scheme

            candidate_favicon_uri = "{}://{}/favicon.ico".format(original_scheme, original_domain)

            mc = MementoClient()

            try:
                memento_info = mc.get_memento_info(candidate_favicon_uri, self.memento_datetime)

                if "mementos" in memento_info:
                    if "closest" in memento_info["mementos"]:
                        if "uri" in memento_info["mementos"]["closest"]:
                            self.original_link_favicon_uri = memento_info["mementos"]["closest"]["uri"][0]

            except Exception as e:
                # it appears that MementoClient throws 
                self.logger.info("got an exception while searching for the original favicon at {}: {}".format(candidate_favicon_uri, repr(e)))

        self.logger.debug("discovered favicon at {}".format(self.original_link_favicon_uri))

        return self.original_link_favicon_uri




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

        self.logger.info("getting Lede3 description for URI {}".format(self.uri))

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

        adimagelist = [
            'altfarm.mediaplex.com',
            's0b.bluestreak.com',
            'ad.doubleclick.net'
        ]

        if self.image_list == None:

            self.image_list = {}

            self.logger.debug("discovering all images at {}".format(self.uri))

            for imgtag in self.soup.find_all("img"):

                imageuri = urljoin(self.uri, imgtag.get("src"))

                evalimage = True

                for addomain in adimagelist:
                    if addomain in imageuri:
                        evalimage = False

                if evalimage == True:

                    if "/ads/" in imageuri.lower():

                        self.logger.warn("discovered string /ads/ in image uri {}, skipping...".format(imageuri))

                    else:

                        if imageuri not in self.image_list:

                            self.logger.debug("examining embedded image at URI {} from resource {}".format(imageuri, self.uri))

                            try:
                                resp = requests.get(imageuri)

                                self.logger.debug("got a response for image URI {}".format(imageuri))

                                imagedata = resp.content

                                self.image_list[imageuri] = imagedata

                            except requests.exceptions.ConnectionError:
                                self.logger.warn("connection error from image at URI {}, skipping...".format(imageuri))
                            except requests.exceptions.TooManyRedirects:
                                self.logger.warn("request for image at URI {} exceeded an acceptable number of redirects, skipping...".format(imageuri))

                else:
                    self.logger.warn("domain of image at URI {} is a known advertising service, skipping...".format(imageuri))

    def _getLargestImage(self):

        maxsize = 0
        maximageuri = None

        self._find_all_images()

        for imageuri in self.image_list:

            p = ImageFile.Parser()

            if self.image_list[imageuri] == None:

                self.logger.warn("no data at image URI {}".format(imageuri))

            else:

                p.feed(self.image_list[imageuri])

                if p.image == None:

                    self.logger.warn("processing image from URI {} produced no data, skipping...".format(imageuri))

                else:
                    width, height = p.image.size

                    imgsize = width * height

                    if imgsize > maxsize:
                        maxsize = imgsize
                        maximageuri = imageuri

        return maximageuri