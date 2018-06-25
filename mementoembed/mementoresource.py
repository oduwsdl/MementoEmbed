import os
import re
import logging
import zipfile
import io

import aiu

from datetime import datetime

from bs4 import BeautifulSoup

wayback_pattern = re.compile('(/[0-9]{14})/')

def memento_resource_factory(urim, http_cache, logger=None):

    response = http_cache.get(urim)

    content = response.text

    soup = BeautifulSoup(content, "html5lib")

    # TODO: META redirects?

    metatags = soup.find_all("meta")

    given_urim = urim

    for tag in metatags:

        if tag.get("http-equiv") == "refresh":

            if tag.get("content"):

                url = [i.strip() for i in tag.get("content").split(';')][1]
                url = url.split('=')[1]
                url = url.strip('"')
                redirect_url = url.strip("'")
                urim = redirect_url

                resp = http_cache.get(urim)

                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html5lib")

    # maybe we search for /[0-9]{14}/ in the URI and then try id_
    if wayback_pattern.search(urim):
        candidate_raw_urim = wayback_pattern.sub(r'\1id_/', urim)

        resp = http_cache.get(candidate_raw_urim)

        if resp.status_code == 200:
            return WaybackMemento(http_cache, urim, logger=logger, given_uri=given_urim)

    if soup.find("iframe", {"id": "theWebpage"}):
        return IMFMemento(http_cache, urim, logger=logger, given_uri=given_urim)
    
    if soup.find("div", {'id': 'SOLID'}):
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

    @property
    def content(self):
        return self.response.text

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

        response = self.http_cache.get(self.raw_urim)

        return response.text
