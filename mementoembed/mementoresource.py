
import os
import re
import zipfile
import io

import aiu

from datetime import datetime

from bs4 import BeautifulSoup
from bs4 import Comment

wayback_pattern = re.compile('(/[0-9]{14})/')

def memento_resource_factory(urim, http_cache):

    response = http_cache.get(urim)

    content = response.text

    soup = BeautifulSoup(content, "html5lib")

    # TODO: META redirects?

    # maybe we search for /[0-9]{14}/ in the URI and then try id_
    if wayback_pattern.search(urim):
        candidate_raw_urim = wayback_pattern.sub(r'\1id_/', urim)

        resp = http_cache.get(candidate_raw_urim)

        if resp.status_code == 200:
            return WaybackMemento(http_cache, urim)

    elif soup.find("iframe", {"id": "theWebpage"}):
        return IMFMemento(http_cache, urim)
    
    elif soup.find("div", {'id': 'SOLID'}):
        return ArchiveIsMemento(http_cache, urim)

    else:
        return MementoResource(http_cache, urim)

class MementoResource:

    def __init__(self, http_cache, urim):

        self.http_cache = http_cache
        self.urim = urim

        self.response = self.http_cache.get(self.urim)

        self.urir = None
        self.urig = None
        self.memento_dt = None

    @property
    def memento_datetime(self):
        # TODO: make this a datetime object
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

        bname = os.path.basename(self.urim)
        self.compressed_memento_urim = "http://archive.is/download/{}.zip".format(bname)

        response = self.http_cache.get(self.compressed_memento_urim)

        z = zipfile.ZipFile(io.BytesIO(response.content))

        content = z.read('index.html')

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