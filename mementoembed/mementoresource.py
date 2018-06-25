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

def memento_resource_factory(urim, http_cache, logger=None):

    logger = logger or logging.getLogger(__name__)

    response = http_cache.get(urim)

    content = response.text

    soup = BeautifulSoup(content, "html5lib")

    # TODO: META redirects?

    metatags = soup.find_all("meta")

    given_urim = urim

    for tag in metatags:

        if tag.get("http-equiv") == "refresh":

            logger.info("detected html meta tag redirect in content from URI-M {}".format(urim))

            if tag.get("content"):

                url = [i.strip() for i in tag.get("content").split(';')][1]
                url = url.split('=')[1]
                url = url.strip('"')
                redirect_url = url.strip("'")
                urim = redirect_url

                logger.info("acquiring redirected URI-M {}".format(urim))

                resp = http_cache.get(urim)

                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html5lib")

    # maybe we search for /[0-9]{14}/ in the URI and then try id_
    if wayback_pattern.search(urim):
        logger.info("URI-M {} matches the wayback pattern".format(urim))
        candidate_raw_urim = wayback_pattern.sub(r'\1id_/', urim)

        resp = http_cache.get(candidate_raw_urim)

        if resp.status_code == 200:
            logger.info("memento at {} is a Wayback memento".format(urim))
            return WaybackMemento(http_cache, urim, logger=logger, given_uri=given_urim)

    if soup.find("iframe", {"id": "theWebpage"}):
        logger.info("memento at {} is an IMF memento".format(urim))
        return IMFMemento(http_cache, urim, logger=logger, given_uri=given_urim)
    
    if soup.find("div", {'id': 'SOLID'}):
        logger.info("memento at {} is an Archive.is memento".format(urim))
        return ArchiveIsMemento(http_cache, urim, logger=logger, given_uri=given_urim)

    # fall through to the base class
    return MementoResource(http_cache, urim, logger=logger, given_uri=given_urim)

class MementoResource:

    def __init__(self, http_cache, urim, logger=None, given_uri=None):

        self.logger = logger or logging.getLogger(__name__)

        self.http_cache = http_cache
        self.urim = urim
        self.given_uri = given_uri

        self.response = self.http_cache.get(self.urim)

        self.urir = None
        self.urig = None
        self.memento_dt = None

        self.framecontent = []

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

        soup = BeautifulSoup(self.response.text, 'html5lib')

        # self.framecontent.append(self.response.text)

        frames = soup.findAll("frame")

        for frame in frames:
            urig = None
            frameuri = frame['src']

            o = urlparse(frameuri)

            # deal with relative URIs
            if o.netloc == '':

                frameuri = urljoin(self.original_uri, frameuri)

                timegate_stem = self.timegate[0:self.timegate.find(self.original_uri)]

                if timegate_stem[-1] != '/':
                    urig = '/'.join([timegate_stem, frameuri])

            if urig is None:
                urig = timegate_stem + frameuri

            response = self.http_cache.get(urig, 
                headers={
                    'accept-datetime': self.memento_datetime.strftime("%a, %d %b %Y %H:%M:%S GMT")
                    })

            if response.status_code == 302:
                frameuri = response.headers['location']

            response = self.http_cache.get(frameuri)
            self.framecontent.append(response.text)

        fullcontent = ""

        for content in self.framecontent:
            soup = BeautifulSoup(content, 'html5lib')

            framecontent = ""

            for item in soup.findAll('body'):
                for c in item.children:
                    framecontent += str(c)

            fullcontent += "{}\n".format(framecontent)

        return "<html><body>\n{}</body></html>".format(fullcontent)

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
            
            soup = BeautifulSoup(self.content, "html5lib")

            anchors = soup.find_all('a')

            for a in anchors:
                if a.text == 'download .zip':
                    self.compressed_memento_urim = a['href']
                    break

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

        soup = BeautifulSoup(content, "html5lib")

        twp = soup.find("iframe", {"id": "theWebpage"})

        self.raw_urim = twp.get('src')

        response = self.http_cache.get(self.raw_urim)

        return response.text


class WaybackMemento(MementoResource):

    @property
    def raw_content(self):

        self.raw_urim = wayback_pattern.sub(r'\1id_/', self.urim)

        self.logger.info("using raw URI-M {}".format(self.raw_urim))

        response = self.http_cache.get(self.raw_urim)

        return response.text
