import os
import re
import logging
import zipfile
import io

import aiu

from datetime import datetime
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

wayback_pattern = re.compile('(/[0-9]{14})/')

module_logger = logging.getLogger('mementoembed.mementoresource')

class NotAMementoError(Exception):
    
    def __init__(self, message, response, original_exception=None):
        self.message = message
        self.response = response
        self.original_exception = original_exception

class MementoParsingError(Exception):

    def __init__(self, message, original_exception=None):
        self.message = message
        self.original_exception = original_exception

def memento_resource_factory(urim, http_cache):

    response = http_cache.get(urim)

    content = response.text

    try:
        soup = BeautifulSoup(content, "html5lib")
    except Exception as e:
        raise MementoParsingError(
            "failed to open document using BeautifulSoup",
            original_exception=e)

    try:
        metatags = soup.find_all("meta")
    except Exception as e:
        raise MementoParsingError(
            "failed to parse document using BeautifulSoup",
            original_exception=e)

    given_urim = urim

    for tag in metatags:
        
        try:
            if tag.get("http-equiv") == "refresh":

                module_logger.info("detected html meta tag redirect in content from URI-M {}".format(urim))

                if tag.get("content"):

                    url = [i.strip() for i in tag.get("content").split(';', 1)][1]
                    url = url.split('=', 1)[1]
                    url = url.strip('"')
                    redirect_url = url.strip("'")
                    urim = redirect_url

                    module_logger.info("acquiring redirected URI-M {}".format(urim))

                    resp = http_cache.get(urim)

                    module_logger.debug("for redirected URI-M {}, I got a response of {}".format(urim, resp))
                    module_logger.debug("content: {}".format(resp.text))

                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "html5lib")

        except Exception as e:
            raise MementoParsingError(
                "failed to parse document using BeautifulSoup",
                original_exception=e)

    # maybe we search for /[0-9]{14}/ in the URI and then try id_
    if wayback_pattern.search(urim):
        module_logger.debug("URI-M {} matches the wayback pattern".format(urim))
        candidate_raw_urim = wayback_pattern.sub(r'\1id_/', urim)

        resp = http_cache.get(candidate_raw_urim)

        if resp.status_code == 200:
            module_logger.info("memento at {} is a Wayback memento".format(urim))
            return WaybackMemento(http_cache, urim, given_uri=given_urim)

    if soup.find("iframe", {"id": "theWebpage"}):
        module_logger.info("memento at {} is an IMF memento".format(urim))
        return IMFMemento(http_cache, urim, given_uri=given_urim)
    
    if soup.find("div", {'id': 'SOLID'}):
        module_logger.info("memento at {} is an Archive.is memento".format(urim))
        return ArchiveIsMemento(http_cache, urim, given_uri=given_urim)

    # fall through to the base class
    return MementoResource(http_cache, urim, given_uri=given_urim)

class MementoResource:

    def __init__(self, http_cache, urim, logger=None, given_uri=None):

        self.logger = logging.getLogger('mementoembed.mementoresource.MementoResource')

        self.http_cache = http_cache
        self.urim = urim
        self.given_uri = given_uri

        self.response = self.http_cache.get(self.urim)

        self.urir = None
        self.urig = None
        self.memento_dt = None

        try:
            self.memento_dt = self.memento_datetime
        except KeyError as e:
            raise NotAMementoError("no memento-datetime header", 
                response=self.response, original_exception=e)

        try:
            self.urir = self.original_uri
        except KeyError as e:
            raise NotAMementoError("error parsing link header for original URI",
                response=self.response, original_exception=e)

        try:
            self.urig = self.timegate
        except KeyError as e:
            raise NotAMementoError("error parsing link header for timegate URI",
                response=self.response, original_exception=e)
        
        if 'text/html' not in self.response.headers['content-type']:
            raise MementoParsingError("Cannot process non-HTML content")

        self.framecontent = []
        self.framescontent = None

    @property
    def memento_datetime(self):
        
        if self.memento_dt is None:
            self.memento_dt = datetime.strptime(
                self.response.headers['memento-datetime'], 
                "%a, %d %b %Y %H:%M:%S GMT"
            )
        
        return self.memento_dt

    @property
    def original_uri(self):
        if self.urir is None:
            self.urir = aiu.convert_LinkTimeMap_to_dict( self.response.headers['link'] )['original_uri']

        return self.urir

    @property
    def timegate(self):
        if self.urig is None:
            self.urig = aiu.convert_LinkTimeMap_to_dict( self.response.headers['link'] )['timegate_uri']

        return self.urig

    def get_content_from_frames(self):

        if self.framescontent is None:

            try:
                soup = BeautifulSoup(self.response.text, 'html5lib')
            except Exception as e:
                raise MementoParsingError(
                    "failed to open document using BeautifulSoup",
                    original_exception=e)

            try:
                title = soup.title.text
            except Exception as e:
                raise MementoParsingError(
                    "failed to parse document using BeautifulSoup",
                    original_exception=e)

            self.logger.debug("title is {}".format(title))

            # self.framecontent.append(self.response.text)

            try:
                frames = soup.findAll("frame")
            except Exception as e:
                raise MementoParsingError(
                    "failed to parse document using BeautifulSoup",
                    original_exception=e)

            for frame in frames:
                urig = None
                frameuri = frame['src']

                self.logger.debug("examining frame at {}".format(frameuri))

                o = urlparse(frameuri)

                # deal with relative URIs
                if o.netloc == '':

                    frameuri = urljoin(self.original_uri, frameuri)

                    timegate_stem = self.timegate[0:self.timegate.find(self.original_uri)]

                    if timegate_stem[-1] != '/':
                        urig = '/'.join([timegate_stem, frameuri])

                if urig is None:
                    urig = timegate_stem + frameuri

                accept_datetime_str = self.memento_datetime.strftime("%a, %d %b %Y %H:%M:%S GMT")

                self.logger.debug("using accept-datetime {} with timegate {} ".format(accept_datetime_str, urig))

                response = self.http_cache.get(
                    urig, 
                    headers={
                        'accept-datetime': accept_datetime_str
                        })

                self.logger.debug("request headers are {}".format(response.request.headers))
                self.logger.debug("request url is {}".format(response.request.url))
                self.logger.debug("response is {}".format(response))

                if response.status_code == 200:
                    self.logger.debug("URI endpoint: {}".format(response.url))
                    self.logger.debug("frameuri: {}".format(frameuri))
                    self.framecontent.append(response.text)

            fullcontent = ""

            self.logger.debug("framecontent size: {}".format(len(self.framecontent)))

            for content in self.framecontent:

                try:
                    soup = BeautifulSoup(content, 'html5lib')
                except Exception as e:
                    raise MementoParsingError(
                        "failed to open document using BeautifulSoup",
                        original_exception=e)

                framecontent = ""

                try:
                    for item in soup.findAll('body'):
                        for c in item.children:
                            # self.logger.debug("adding:\n{}".format(str(c)))
                            framecontent += str(c)

                except Exception as e:
                    raise MementoParsingError(
                        "failed to open document using BeautifulSoup",
                        original_exception=e)

                fullcontent += "{}\n".format(framecontent)

            self.framescontent = "<html><head><title>{}</title></head><body>\n{}</body></html>".format(title, fullcontent)
            # self.logger.debug("framescontent:\n{}".format(self.framescontent))

        return self.framescontent

    @property
    def content(self):

        content = self.response.text

        soup = BeautifulSoup(content, 'html5lib')

        # TODO: BeautifulSoup does not seem to handle framesets inside a <body> tag
        frames = soup.findAll("frame")

        if len(frames) > 0:
            content = self.get_content_from_frames()

        return content

    @property
    def raw_content(self):
        return self.content

class ArchiveIsMemento(MementoResource):

    @property
    def raw_content(self):

        # http://archive.is/30uIj
        # http://archive.is/download/30uIj.zip
        # The user-agent matters, if it is not "approved", the resulting zipfile will be corrupt

        if wayback_pattern.search(self.urim):
            
            try:
                soup = BeautifulSoup(self.content, "html5lib")
            except Exception as e:
                raise MementoParsingError(
                    "failed to open document using BeautifulSoup",
                    original_exception=e)

            try:
                anchors = soup.find_all('a')

                for a in anchors:
                    if a.text == 'download .zip':
                        self.compressed_memento_urim = a['href']
                        break

            except Exception as e:
                raise MementoParsingError(
                    "failed to parse document using BeautifulSoup",
                    original_exception=e)

        else:

            bname = os.path.basename(self.urim)
            self.compressed_memento_urim = "http://archive.is/download/{}.zip".format(bname)

        self.logger.info("using compressed memento URI-M of {}".format(self.compressed_memento_urim))

        response = self.http_cache.get(self.compressed_memento_urim)

        z = zipfile.ZipFile(io.BytesIO(response.content))

        content = z.read('index.html')

        self.logger.debug( "from Archive.is type of raw content: {}".format( type(content) ) )
        self.logger.debug("size of raw content: {}".format( len(content) ) )

        return content


class IMFMemento(MementoResource):

    @property
    def raw_content(self):
        
        self.response = self.http_cache.get(self.urim)

        content = self.response.text

        try:
            soup = BeautifulSoup(content, "html5lib")
        except Exception as e:
            raise MementoParsingError(
                "failed to open document using BeautifulSoup",
                original_exception=e)

        try:
            twp = soup.find("iframe", {"id": "theWebpage"})
        except Exception as e:
            raise MementoParsingError(
                "failed to parse document using BeautifulSoup",
                original_exception=e)

        self.raw_urim = twp.get('src')

        response = self.http_cache.get(self.raw_urim)

        return response.text


class WaybackMemento(MementoResource):

    @property
    def raw_content(self):

        try:
            soup = BeautifulSoup(self.response.text, 'html5lib')
        except Exception as e:
            raise MementoParsingError(
                "failed to open document using BeautifulSoup",
                original_exception=e)

        try:
            frames = soup.findAll("frame")
        except Exception as e:
            raise MementoParsingError(
                "failed to parse document using BeautifulSoup",
                original_exception=e)

        if len(frames) > 0:

            framecontent = self.get_content_from_frames()
            return framecontent

        else:
            self.raw_urim = wayback_pattern.sub(r'\1id_/', self.urim)
            self.logger.debug("using raw URI-M {}".format(self.raw_urim))
            response = self.http_cache.get(self.raw_urim)
            return response.text
