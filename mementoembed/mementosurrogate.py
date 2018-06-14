import sys
import re
import base64

import requests
from requests_futures.sessions import FuturesSession
import tldextract
import aiu

from datetime import datetime
from urllib.parse import urljoin, urlparse

from PIL import ImageFile
from bs4 import BeautifulSoup
from readability import Document
from justext import justext, get_stoplist
from memento_client import MementoClient

p = re.compile(' +')

archive_collection_patterns = [
    "http://wayback.archive-it.org/([0-9]*)/[0-9]{14}/.*",
]

archive_collection_uri_prefixes = {
    "Archive-It": "https://archive-it.org/collections/{}"
}

archive_names = {
    "archive-it.org": "Archive-It",
    "archive.org": "Internet Archive",
    "webcitation.org": "WebCite",
    "archive.is": "archive.today"
}

def get_favicon_from_html(content):
    # search HTML for meta tags containing the relation "icon" or "shortcut"
    
    favicon_uri = None

    soup = BeautifulSoup(content, 'html5lib')

    links = soup.find_all("link")

    for link in links:

        if 'icon' in link['rel']:
            favicon_uri = link['href']
            break

    # if that fails, try the older, nonstandard relation 'shortcut'
    if favicon_uri == None:

        for link in links:

            if 'shortcut' in link['rel']:
                favicon_uri = link['href']
                break

    return favicon_uri

def get_favicon_from_google_service(session, uri):
    """
        Get the favicon from the Google service.

        This is a last-ditch effort to get a favicon.

        The Google service returns a default if it has no URI in the cache.
    """

    favicon_uri = None

    domain = tldextract.extract(uri).registered_domain

    google_favicon_uri = "https://www.google.com/s2/favicons?domain={}".format(domain)

    r = session.get(google_favicon_uri)

    if r.status_code == 200:
        favicon_uri == google_favicon_uri

    return favicon_uri

class NotMementoException(Exception):
    # TODO: raise this exception
    pass

class MementoConnectionError(Exception):
    # TODO: raise this exception, it should generate a 503
    pass

class MementoConnectionTimeout(Exception):
    # TODO: raise this exception, it should generate a 504
    pass

class MementoImageConnectionError(Exception):
    # TODO: raise this exception, it should generate a 503
    pass

class MementoImageConnectionTimeout(Exception):
    # TODO: raise this exception, it should generate a 504
    pass

class MementoContentParseError(Exception):
    """ Something went wrong parsing the Memento Content """
    pass


class MementoSurrogate:
    """
        Surrogate generates and stores all information about surrogates
        related to content, uri, and response_headers.
    """

    def __init__(self, urim, session=requests.session(), img_pattern_blocklist=[], 
        user_agent_string="Mozilla/5.0 (Windows NT 6.1; rv:27.3) Gecko/20130101 Firefox/27.3", 
        working_directory="/tmp/mementosurrogate", logger=None):
        """
            This constructor requires the `urim` argument.

            Optional arguments:
            * `session` - a requests session object (useful for testing or specifying an external cache)
            * `img_pattern_blocklist` - a Python list containing a series of patterns to use when discarding images
            * `working_directory` - the directory to use on disk when writing out or reading files
            * `logger` - a Python logging object
        """

        self.surrogate_creation_time = None
        self.surrogate_creation_time = self.creation_time

        self.urim = urim
        self.content = None

        self.response_headers = None

        self.soup = None

        self.text_snippet_string = None
        self.striking_image_uri = None
        self.title_string = None
        self.image_list = None
        self.site_favicon_uri = None
        self.logger = logger

        self.urir = None
        self.original_domainname = None
        self.original_scheme_string = None
        self.original_link_status_text = None
        self.original_link_favicon_uri = None
        self.memento_dt = None
        self.urig = None

        self.archive_favicon_uri = None
        self.archive_collection_name = None
        self.archive_collection_uri = None
        self.archive_collection_id = None
        self.memento_archive_name = None
        self.memento_archive_uri = None
        self.memento_archive_domain = None
        self.memento_archive_scheme = None

        self.session = session
        self.working_directory = working_directory

        self.img_pattern_blocklist = img_pattern_blocklist
        self.user_agent_string = user_agent_string

        self.newcontent = None
        

    def fetch_memento(self):

        if self.content == None or self.response_headers == None:

            self.logger.debug("attempting to fetch memento at {}".format(self.urim))

            response = self.session.get(self.urim, headers={'User-Agent': self.user_agent_string})
        
            self.content = response.text

            self.logger.debug("content size is {}".format(len(self.content)))

            self.soup = BeautifulSoup(self.content, "html5lib")

            metatags = self.soup.find_all("meta")

            for tag in metatags:

                if tag.get("http-equiv") == "refresh":

                    self.logger.warning("discovered a meta-tag refresh in memento at {}".format(self.urim))
                    
                    if tag.get("content"):    

                        try:

                            url = [i.strip() for i in tag.get("content").split(';')][1]
                            url = url.split('=')[1]
                            url = url.strip('"')
                            redirect_url = url.strip("'")

                            self.logger.debug("discovered new URI at {}, fetching".format(redirect_url))

                            real_response = self.session.get(redirect_url, 
                                headers={'User-Agent': self.user_agent_string})
                            
                            self.content = real_response.text
                            self.soup = BeautifulSoup(self.content, "html5lib")

                            self.logger.debug("content size is now {}".format(len(self.content)))

                        except Exception as e:
                            self.logger.error("error in processing memento at {}: {}".format(self.urim, e))
                            raise MementoContentParseError(
                                "Could not parse content for memento at {}".format(self.urim)
                            )

            # for Internet Memory Foundation sites, the real content is inside an iframe
            twp = self.soup.find("iframe", {"id": "theWebpage"})

            if twp:
                self.logger.warning("discovered an IMF web site, making adjustments...")
                real_urim = twp.get('src')

                self.logger.debug("fetching actual memento content at {}".format(real_urim))
                real_response = self.session.get(real_urim, headers={'User-Agent': self.user_agent_string})

                # replace the content downloaded, but keep the headers
                # self.newcontent = repr(real_response)
                self.content = real_response.text
                # self.soup = BeautifulSoup(self.newcontent, "html5lib")
                self.soup = BeautifulSoup(self.content, "html5lib")

                # self.logger.debug("content size is now {}".format(len(self.newcontent)))
                self.logger.debug("content size is now {}".format(len(self.content)))

            # for archive.is, the real content is inside of a div with an id of SOLID
            # solid = self.soup.find("div", {'id': 'SOLID'})

            # if solid:
            #     self.logger.warning("discovered an archive.is web site, making adjustments...")
                
            #     # self.newcontent = repr(solid)
            #     self.content = repr(solid)
            #     # self.soup = BeautifulSoup(self.newcontent, "html5lib")
            #     self.soup = BeautifulSoup(self.content, "html5lib")

            #     # self.logger.debug("content size is now {}".format(len(self.newcontent)))
            #     self.logger.debug("content size is now {}".format(len(self.content)))

            self.response_headers = response.headers

            if not MementoClient.is_memento(self.urim, response=response):
                raise NotMementoException("URI {} has no memento headers".format(self.urim))

    @property
    def text_snippet(self):
        """
            Acquires a test snippet for the surrogate.

            1. tries the "description" field of the HTML meta tag
            2. tries the "og:description" field of the HTML meta tag
            3. tries the "twitter:description" field of the HTML met tag
            4. falls back to Lede3
        """

        self.fetch_memento()

        self.logger.info("selecting text snippet for {}".format(self.urim))

        if self.text_snippet_string == None or self.text_snippet_string == "":

            self.text_snippet_string = self._getMetadataDescription()

        if self.text_snippet_string == None or self.text_snippet_string == "":

            self.text_snippet_string = self._getMetadataOGDescription()

        if self.text_snippet_string == None or self.text_snippet_string == "":

            self.text_snippet_string = self._getMetadataTwitterDescription()

        if self.text_snippet_string == None or self.text_snippet_string == "":

            self.text_snippet_string = self._getLede3Description()

        # self.text_snippet_string = self.text_snippet_string.strip().replace('\n', ' ').replace('\r', ' ')

        self.text_snippet_string = " ".join(self.text_snippet_string.split())

        if len(self.text_snippet_string) > 197:
            return "{}...".format(self.text_snippet_string[0:197])
        else:
            return self.text_snippet_string

    @property
    def striking_image(self):
        """
            Acquires a striking image for the surrogate.

            1. tries the "og:image" field of the HTML meta tag
            2. tries the "twitter:image" field of the HTML met tag
            3. falls back to largest image by pixels
        """

        self.fetch_memento()
        
        self.logger.info("selecting striking image for {}".format(self.urim))

        if self.striking_image_uri == None or self.striking_image_uri == "":

            self.striking_image_uri = self._getMetadataOGImage()

        if self.striking_image_uri == None or self.striking_image_uri == "":

            self.striking_image_uri = self._getMetadataTwitterImage()

        if self.striking_image_uri == None or self.striking_image_uri == "":

            self.striking_image_uri = self._getLargestImage()

        self.logger.info("selected image at URI-M {}".format(self.striking_image_uri))

        return self.striking_image_uri

    @property
    def title(self):
        """
            Acquires a title from the HTML for the surrogate.

            If no title, responds with "NO TITLE DETECTED"
        """

        self.fetch_memento()

        self.logger.debug("selecting title for {}".format(self.urim))

        if self.title_string == None:

            try:
                title = self.soup.title.string

                self.title_string = " ".join(title.split())

            except AttributeError:
                self.logger.warning("No title detected in HTML for page, falling back to default statement")
                self.title.string = "NO TITLE DETECTED"

        return self.title_string

    @property
    def original_uri(self):
        """
            Acquires the original URI from the memento by interrogating the HTTP Link header.
        """

        self.fetch_memento()

        if self.urir == None:
            self.urir = aiu.convert_LinkTimeMap_to_dict( self.response_headers['link'] )['original_uri']

        return self.urir

    @property
    def timegate(self):
        """
            Acquires the timegate from the memento by interrogating the HTTP Link header.
        """

        self.fetch_memento()

        if self.urig == None:
            self.urig = aiu.convert_LinkTimeMap_to_dict( self.response_headers['link'] )['timegate_uri']

        return self.urig

    @property
    def original_domain(self):
        """
            Generates the original domain name for the memento.
        """

        if self.original_domainname == None:
            o = urlparse(self.original_uri)
            original_domain = o.netloc

            self.original_domainname = original_domain

        return self.original_domainname

    @property
    def original_scheme(self):
        """
            Generates the original scheme for the memento.
        """

        if self.original_scheme_string == None:
            
            urir = self.original_uri

            o = urlparse(urir)
            original_scheme = o.scheme

            self.original_scheme_string = original_scheme

        return self.original_scheme_string

    @property
    def original_link_status(self):
        """
            Checks the link status of the original URI related to this memento.
        """

        if self.original_link_status_text == None:

            try:
                r = self.session.get(self.original_uri, headers={'User-Agent': self.user_agent_string})

                if r.status_code == 200:
                    self.original_link_status_text = "Live"
                else:
                    self.original_link_status_text = "Rotten"

            except Exception:
                self.original_link_status_text = "Rotten"

        return self.original_link_status_text

    @property
    def memento_datetime(self):
        """
            Extracts the memento datetime from this memento's headers.
        """

        self.fetch_memento()

        if self.memento_dt == None:
            self.memento_dt = datetime.strptime(
                self.response_headers['memento-datetime'], "%a, %d %b %Y %H:%M:%S GMT")
            
        return self.memento_dt

    @property
    def original_favicon(self):
        """
            Acquires the favicon of the original resource by trying several different methods.
        """

        self.fetch_memento()

        # 1. try the HTML within the memento for a favicon
        if self.original_link_favicon_uri == None:
            self.logger.info("interrogating HTML of memento for favicon URI")

            self.original_link_favicon_uri = get_favicon_from_html(self.content)

            if self.original_link_favicon_uri:

                if self.original_link_favicon_uri[0:4] != 'http':
                    # in this case we have a relative link
                    self.original_link_favicon_uri = urljoin(self.urim, self.original_link_favicon_uri)

                # TODO: what if the favicon discovered this way is not a memento? - we use datetime negotiation
                self.logger.debug("using favicon discovered by interrogating HTML: {}".format(self.original_link_favicon_uri))

        # 2. try to construct the favicon URI and look for it in the archive
        candidate_favicon_uri = "{}://{}/favicon.ico".format(
                self.original_scheme, self.original_domain)

        if self.original_link_favicon_uri == None:
            self.logger.info("querying web archive for original favicon at conventional URI")

            favicon_timegate = "{}/{}".format(
                self.timegate[0:self.timegate.find(self.original_uri)],
                candidate_favicon_uri)

            self.logger.debug("using URI-G of {}".format(favicon_timegate))

            mc = MementoClient(timegate_uri=favicon_timegate, check_native_timegate=False)

            try:
                memento_info = mc.get_memento_info(candidate_favicon_uri, self.memento_datetime)

                if "mementos" in memento_info:

                    if "closest" in memento_info["mementos"]:

                        if "uri" in memento_info["mementos"]["closest"]:
                            candidate_memento_favicon_uri = memento_info["mementos"]["closest"]["uri"][0]

                            r = self.session.get(self.original_link_favicon_uri, headers={'User-Agent': self.user_agent_string})

                            if r.status_code == 200:

                                if 'image/' in r.headers['content-type']:

                                    self.logger.debug("using favicon discovered through datetime negotiation: {}".format(candidate_memento_favicon_uri))
                                    self.original_link_favicon_uri = candidate_memento_favicon_uri

            except Exception as e:
                # it appears that MementoClient throws 
                self.logger.info("got an exception while searching for the original favicon at {}: {}".format(candidate_favicon_uri, repr(e)))
                self.original_link_favicon_uri = None

        # 3. request the home page of the site on the live web and look for favicon in its HTML
        if self.original_link_favicon_uri == None:
            live_site_uri = "{}://{}".format(self.original_scheme, self.original_domain)

            r = self.session.get(live_site_uri, headers={'User-Agent': self.user_agent_string})

            candidate_favicon_uri_from_live = get_favicon_from_html(r.text)

            if candidate_favicon_uri_from_live:

                if candidate_favicon_uri_from_live[0:4] != 'http':
                    self.original_link_favicon_uri = urljoin(live_site_uri, candidate_favicon_uri_from_live)

        # 4. try to construct the favicon URI and look for it on the live web
        if self.original_link_favicon_uri == None:

            r = self.session.get(candidate_favicon_uri, headers={'User-Agent': self.user_agent_string})

            if r.status_code == 200:

                # this is some protection against soft-404s
                if 'image/' in r.headers['content-type']:
                    self.original_link_favicon_uri = candidate_favicon_uri
        
        # 5. if all else fails, fall back to the Google favicon service
        if self.original_link_favicon_uri == None:

            self.original_link_favicon_uri = get_favicon_from_google_service(self.session, self.urim)

        self.logger.debug("discovered memento favicon at {}".format(self.original_link_favicon_uri))

        return self.original_link_favicon_uri

    @property
    def archive_favicon(self):
        """
            Acquires the favicon for the archive by using several different methods.
        """

        self.fetch_memento()

        # 1 try the HTML within the archive's web page for a favicon
        if self.archive_favicon_uri == None:
            
            self.logger.debug("attempting to acquire the archive favicon URI from HTML")

            r = self.session.get(self.archive_uri, headers={'User-Agent': self.user_agent_string})

            self.archive_favicon_uri = get_favicon_from_html(r.text)

        # 2. try to construct the favicon URI and look for it on the live web
        if self.archive_favicon_uri == None:

            self.logger.debug("attempting to use the conventional favicon URI to find the archive favicon URI")

            candidate_favicon_uri = "{}://{}/favicon.ico".format(self.archive_scheme, self.archive_domain)

            r = self.session.get(candidate_favicon_uri, headers={'User-Agent': self.user_agent_string})

            if r.status_code == 200:

                # this is some protection against soft-404s
                if 'image/' in r.headers['content-type']:
                    self.archive_favicon_uri = candidate_favicon_uri

        # 3. if all else fails, fall back to the Google favicon service
        if self.archive_favicon_uri == None:

            self.logger.debug("attempting to query the google favicon service for the archive favicon URI")

            self.archive_favicon_uri = get_favicon_from_google_service(
                self.session, self.archive_uri)

        self.logger.debug("discovered archive favicon at {}".format(self.archive_favicon_uri))

        return self.archive_favicon_uri

    @property
    def archive_scheme(self):
        """
            Derives the scheme of the memento's archive URI.
        """

        self.fetch_memento()

        if self.memento_archive_scheme == None:

            o = urlparse(self.urim)
            self.memento_archive_scheme = o.scheme

        return self.memento_archive_scheme

    @property
    def archive_domain(self):
        """
            Derives the domain of the memento's archive URI.
        """

        self.fetch_memento()

        if self.memento_archive_domain == None:
            self.memento_archive_domain = tldextract.extract(self.archive_uri).registered_domain

        return self.memento_archive_domain

    @property
    def archive_uri(self):
        """
            Generates the URI of the memento's archive.
        """

        self.fetch_memento()

        if self.memento_archive_uri == None:
            o = urlparse(self.urim)
            domain = tldextract.extract(self.urim).registered_domain

            self.memento_archive_uri = "{}://{}".format(o.scheme, domain)

        return self.memento_archive_uri

    @property
    def archive_name(self):
        """
            Generates the name of the archive, first using known archive names,
            then falling back to the domain name of the archive.
        """

        self.fetch_memento()

        if self.memento_archive_name == None:

            if self.archive_domain in archive_names:

                self.memento_archive_name = archive_names[self.archive_domain]

            else:

                self.memento_archive_name = self.archive_domain.upper()
        
        return self.memento_archive_name

    @property
    def collection_uri(self):
        """
            Generates the collection URI, if possible, falling back to None otherwise.
        """

        self.fetch_memento()

        if self.archive_collection_uri == None:

            if self.collection_id:

                try:
                    self.archive_collection_uri = archive_collection_uri_prefixes[self.archive_name].format(
                        self.collection_id)
                except KeyError:
                    self.archive_collection_uri = None

        return self.archive_collection_uri

    @property
    def collection_name(self):
        """
            Acquires the collection name, if possible, falling back to None otherwise.
        """

        self.fetch_memento()

        if self.archive_collection_name == None:

            if self.collection_id:

                aic = aiu.ArchiveItCollection(
                    collection_id=self.collection_id,
                    logger=self.logger,
                    working_directory=self.working_directory
                    )

                self.archive_collection_name = aic.get_collection_name()

        return self.archive_collection_name

    @property
    def collection_id(self):
        """
            Generates the collection URI, if possible, falling back to None otherwise.
        """

        self.fetch_memento()

        if self.archive_collection_id == None:

            for pattern in archive_collection_patterns:
                m = re.match(pattern, self.urim)

                if m:
                    self.archive_collection_id = m.group(1)
                    break

        return self.archive_collection_id

    @property
    def creation_time(self):

        if self.surrogate_creation_time == None:
            self.surrogate_creation_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        return self.surrogate_creation_time

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

        self.logger.info("getting Lede3 description for URI {}".format(self.urim))

        description = None

        doc = Document(self.content)

        d = doc.score_paragraphs()

        maxscore = 0
        maxpara = None

        for para in d:

            if d[para]['content_score'] > maxscore:
                maxpara = d[para]['elem']
                maxscore = d[para]['content_score']

        if maxpara is not None:
            allparatext = maxpara.text_content().replace('\n', ' ').replace('\r', ' ').strip()
            description = p.sub(' ', allparatext)
        else:
            paragraphs = justext(self.content, get_stoplist("English"))

            allparatext = ""
            
            for paragraph in paragraphs:

                if not paragraph.is_boilerplat:

                    allparatext += " {}".format(paragraph.text)

            if allparatext == "":

                for paragraph in paragraphs:

                    allparatext += "{}".format(paragraph.text)
            
            if allparatext != "":
                description = allparatext.strip()
            else:
                description = self.soup.get_text()

        return description
        
    def _find_all_images(self):

        if self.image_list == None:

            self.image_list = {}

            self.logger.debug("discovering all images at {}".format(self.urim))

            for imgtag in self.soup.find_all("img"):

                imageuri = urljoin(self.urim, imgtag.get("src"))

                self.logger.debug("evaluating image at URI {}".format(imageuri))

                evalimage = True

                for pattern in self.img_pattern_blocklist:
                    # TODO: support globbing?
                    if pattern in imageuri:
                        evalimage = False
                        self.logger.warning("ignoring image at {}".format(imageuri))

                if imgtag.get('class'):

                    for c in imgtag.get('class'):
                        if 'sprite' in c:
                            evalimage = False
                            break

                if evalimage == True:

                    # if "/ads/" in imageuri.lower():

                    #     self.logger.warning("discovered string /ads/ in image uri {}, skipping...".format(imageuri))

                    # else:

                    if imageuri not in self.image_list:

                        self.logger.debug("examining embedded image at URI {} from resource {}".format(imageuri, self.urim))

                        try:

                            if imageuri[0:5] == 'data:':

                                if 'base64' in imageuri:
                                    imagedata = imageuri.split(',')[1]
                                    imagedata = base64.b64decode(imagedata)
                                else:
                                    self.logger.warning("no supported decoding scheme for image at {}, skipping...".format(imageuri))
                                    continue

                            else:

                                resp = self.session.get(imageuri, headers={'User-Agent': self.user_agent_string})

                                self.logger.debug("got a response for image URI {}".format(imageuri))

                                imagedata = resp.content

                            self.image_list[imageuri] = imagedata

                        except requests.exceptions.ConnectionError:
                            self.logger.warning("connection error from image at URI {}, skipping...".format(imageuri))
                        except requests.exceptions.TooManyRedirects:
                            self.logger.warning("request for image at URI {} exceeded an acceptable number of redirects, skipping...".format(imageuri))

                self.logger.debug("we have {} images in the list so far".format(len(self.image_list)))

                # just do the first 10
                if len(self.image_list) > 15:
                    self.logger.debug("we have {} images, returning...".format(len(self.image_list)))
                    break

                else:
                    self.logger.warning("domain of image at URI {} is a known advertising service, skipping...".format(imageuri))

    def _getLargestImage(self):

        maxsize = 0
        maximageuri = None

        self._find_all_images()

        for imageuri in self.image_list:

            p = ImageFile.Parser()

            if self.image_list[imageuri] == None:

                self.logger.warning("no data at image URI {}".format(imageuri))

            else:

                p.feed(self.image_list[imageuri])

                if p.image == None:

                    self.logger.warning("processing image from URI {} produced no data, skipping...".format(imageuri))

                else:
                    width, height = p.image.size

                    imgsize = width * height

                    if imgsize > maxsize:
                        maxsize = imgsize
                        maximageuri = imageuri

        self.logger.debug("sending back image at URI-M {}".format(maximageuri))

        return maximageuri