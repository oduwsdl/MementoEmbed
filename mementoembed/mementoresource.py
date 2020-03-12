import os
import re
import logging
import zipfile
import io

import aiu

from datetime import datetime
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from requests.exceptions import Timeout, TooManyRedirects, \
    ChunkedEncodingError, ContentDecodingError, StreamConsumedError, \
    URLRequired, MissingSchema, InvalidSchema, InvalidURL, \
    UnrewindableBodyError, ConnectionError, SSLError, ReadTimeout, \
    ConnectionError

wayback_pattern = re.compile('(/[0-9]{14})/')

module_logger = logging.getLogger('mementoembed.mementoresource')

class MementoResourceError(Exception):

    user_facing_error = "There is a problem with this memento."

    def __init__(self, message, original_exception=None):
        self.message = message
        self.original_exception = original_exception

class MementoContentError(MementoResourceError):
    user_facing_error = "There was a problem encountered while processing the content of memento."
    pass

class MementoParsingError(MementoContentError):
    user_facing_error = "There was a problem processing the text content of memento."
    pass

class MementoURINotAtArchiveFailure(MementoResourceError):
    user_facing_error = "The archive did not respond properly for this memento. Maybe it does not exist at this archive?"

    def __init__(self, message, response, original_exception=None):
        self.message = message
        self.response = response
        self.original_exception = original_exception

class NotAMementoError(MementoContentError):
    user_facing_error = "The URI submitted does not appear to belong to a memento."
    
    def __init__(self, message, response, original_exception=None):
        self.message = message
        self.response = response
        self.original_exception = original_exception

class MementoMetaRedirectParsingError(MementoContentError):
    user_facing_error = "This memento appears to have an HTML redirect. There was a problem following the redirect."
    pass

class MementoFramesParsingError(MementoContentError):
    user_facing_error = "This memento appears to have frames. There was a problem discovering the content within these frames."
    pass

class MementoConnectionError(MementoResourceError):
    user_facing_error = "The system had connection problems while retrieving the URI you provided"
    pass

class MementoTimeoutError(MementoConnectionError):
    user_facing_error = "The system timed out trying to reach the URI you provided."
    pass

class MementoConnectionFailure(MementoConnectionError):
    user_facing_error = "The system had connection problems while retrieving the URI you provided"
    pass

class MementoInvalidURI(MementoConnectionError):
    user_facing_error = "The URI you provided appears to be invalid."
    pass

class MementoSSLError(MementoConnectionError):
    user_facing_error = "There was a problem processing the certificate for the URI you provided."
    pass

def get_memento_datetime_from_response(response):

    memento_dt = None

    try:
        memento_dt = datetime.strptime(
                response.headers['memento-datetime'], 
                "%a, %d %b %Y %H:%M:%S GMT"
            )
    except KeyError as e:

        if response.status_code != 200:
            raise MementoURINotAtArchiveFailure("non-200 status code returned",
                response=response, original_exception=e)

        else:
            raise NotAMementoError("no memento-datetime header", 
                response=response, original_exception=e)

    return memento_dt

def get_timegate_from_response(response):

    urig = None

    try:
        # urig = aiu.convert_LinkTimeMap_to_dict(
        #     response.headers['link'] )['timegate_uri']
        urig = response.links['timegate']['url']
    except KeyError as e:
        raise NotAMementoError(
            "link header could not be parsed for timegate URI",
            response=response, original_exception=e)

    return urig

def get_original_uri_from_response(response):

    urir = None

    try:
        # urir = aiu.convert_LinkTimeMap_to_dict(
        #     response.headers['link'] )['original_uri']
        urir = response.links['original']['url']
    except KeyError as e:
        raise NotAMementoError(
            "link header could not be parsed for original URI",
            response=response, original_exception=e)
    except aiu.timemap.MalformedLinkFormatTimeMap as e:
        module_logger.exception("Failed to process link header for URI-R, link header: {}".format(response.headers['link']))

    return urir

def get_memento(http_cache, urim):

    try:
        return http_cache.get(urim)

    except (URLRequired, MissingSchema, InvalidSchema, InvalidURL) as e:
        raise MementoInvalidURI("", original_exception=e)

    except (Timeout, ReadTimeout) as e:
        raise MementoTimeoutError("", original_exception=e)

    except SSLError as e:
        raise MementoSSLError("", original_exception=e)
        
    except (UnrewindableBodyError, ConnectionError) as e:
        raise MementoConnectionFailure("", original_exception=e)

def memento_resource_factory(urim, http_cache):

    response = get_memento(http_cache, urim)

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
        
        if tag.parent.name != 'noscript':

            try:
                if tag.get("http-equiv") == "refresh":

                    module_logger.info("detected html meta tag redirect in content from URI-M")

                    if tag.get("content"):

                        redir_info = [i.strip() for i in tag.get("content").split(';', 1)]

                        # make sure the page isn't just refreshing itself 
                        # periodically
                        if len(redir_info) > 1:

                            rtimeout = redir_info[0]

                            # if the page redirects in more than 60 seconds, we 
                            # assume the user is expected to read it, meaning
                            # it contains actual content and is not just a 
                            # pass-through
                            if int(rtimeout) < 30:

                                url = redir_info[1]
                                url = url.split('=', 1)[1]
                                url = url.strip('"')
                                redirect_url = url.strip("'")
                                urim = redirect_url

                                module_logger.info("acquiring redirected URI-M {}".format(urim))

                                resp = http_cache.get(urim)

                                module_logger.debug("for redirected URI-M {}, I got a response of {}".format(urim, resp))

                                if resp.status_code == 200:
                                    soup = BeautifulSoup(resp.text, "html5lib")

            except Exception as e:
                raise MementoMetaRedirectParsingError(
                    "failed to parse document using BeautifulSoup",
                    original_exception=e)

    if soup.find("iframe", {"id": "theWebpage"}):
        module_logger.info("memento is an IMF memento")
        return IMFMemento(http_cache, urim, given_uri=given_urim)
    
    if soup.find("div", {'id': 'SOLID'}):
        module_logger.info("memento is an Archive.is memento")
        return ArchiveIsMemento(http_cache, urim, given_uri=given_urim)

    # we search for /[0-9]{14}/ in the URI and then try id_
    if wayback_pattern.search(urim):
        module_logger.debug("URI-M {} matches the wayback pattern".format(urim))

        o = urlparse(urim)

        # TODO: find a way to detect all Webrecorder instances, not just webrecorder.io
        if o.netloc == 'webrecorder.io':

            real_urim = urim.replace('{}://webrecorder.io'.format(o.scheme), '{}://content.webrecorder.io'.format(o.scheme))
            real_urim = wayback_pattern.sub(r'\1mp_/', real_urim)

            candidate_raw_urim = wayback_pattern.sub(r'\1id_/', urim)

            resp = http_cache.get(candidate_raw_urim)

            if resp.status_code == 200:
                module_logger.info("memento is a Webrecorder.io memento")
                return WaybackMemento(http_cache, real_urim, given_uri=given_urim)

        else:

            module_logger.info("response history size is {}".format(len(response.history)))

            if len(response.history) == 0:
                candidate_raw_urim = wayback_pattern.sub(r'\1id_/', urim)
            else:
                candidate_raw_urim = wayback_pattern.sub(r'\1id_/', response.url)

            module_logger.info("candidate_raw_urim is {}".format(candidate_raw_urim))

            resp = http_cache.get(candidate_raw_urim)

            if resp.status_code == 200:
                module_logger.info("memento is a Wayback memento")
                return WaybackMemento(http_cache, urim, given_uri=given_urim)

    # if we got here, we haven't categorized the URI-M into an Archive type yet
    # it might be a "hash-style" memento that actually resolves to a Wayback
    memento_dt = get_memento_datetime_from_response(response)

    # TODO: make this unnecessary, it is solely here for memento header testing
    urir = get_original_uri_from_response(response)

    mdt = datetime.strftime(memento_dt, "%a, %d %b %Y %H:%M:%S GMT")
    urig = get_timegate_from_response(response)
    tg_resp = http_cache.get(urig, headers={"accept-datetime": mdt})
    candidate_urim = tg_resp.url

    if wayback_pattern.search(candidate_urim):
        module_logger.debug("derived URI-M {} matches the wayback pattern".format(candidate_urim))
        candidate_raw_urim = wayback_pattern.sub(r'\1id_/', candidate_urim)

        resp = http_cache.get(candidate_raw_urim)
        urim = candidate_urim

        if resp.status_code == 200:
            module_logger.info("derived URI-M {} is a Wayback memento".format(urim))
            return WaybackMemento(http_cache, urim, given_uri=given_urim)

    # fall through to the base class
    return MementoResource(http_cache, urim, given_uri=given_urim)

class MementoResource:

    def __init__(self, http_cache, urim, logger=None, given_uri=None):

        self.logger = logging.getLogger('mementoembed.mementoresource.MementoResource')

        self.http_cache = http_cache
        self.urim = urim
        self.im_urim = urim
        self.given_uri = given_uri

        self.response = get_memento(self.http_cache, self.urim)

        self.urir = None
        self.urig = None
        self.memento_dt = None

        self.memento_dt = self.memento_datetime
        self.urir = self.original_uri
        self.urig = self.timegate
        
        if 'text/html' not in self.response.headers['content-type']:
            module_logger.error("Cannot process non-HTML mementos")
            raise MementoParsingError("Cannot process non-HTML content")

        self.framecontent = []
        self.framescontent = None

    @property
    def memento_datetime(self):
        
        if self.memento_dt is None:
            self.memento_dt = get_memento_datetime_from_response(
                self.response
            )
        
        return self.memento_dt

    @property
    def original_uri(self):
        if self.urir is None:
            self.urir = get_original_uri_from_response(self.response)

        return self.urir

    @property
    def timegate(self):
        if self.urig is None:
            self.urig = get_timegate_from_response(self.response)

        return self.urig

    def get_content_from_frames(self):

        if self.framescontent is None:

            try:
                soup = BeautifulSoup(self.response.text, 'html5lib')
            except Exception as e:
                module_logger.exception("failed to open document using BeautifulSoup")
                raise MementoFramesParsingError(
                    "failed to open document using BeautifulSoup",
                    original_exception=e)

            try:
                title = soup.title.text
            except Exception as e:
                module_logger.exception("failed to extract title using BeautifulSoup")
                raise MementoFramesParsingError(
                    "failed to extract title using BeautifulSoup",
                    original_exception=e)

            self.logger.debug("title is {}".format(title))

            # self.framecontent.append(self.response.text)

            try:
                frames = soup.findAll("frame")
            except Exception as e:
                module_logger.exception("failed to find frames using BeautifulSoup")
                raise MementoFramesParsingError(
                    "failed to find frames using BeautifulSoup",
                    original_exception=e)

            for frame in frames:
                urig = None
                frameuri = frame['src']

                self.logger.debug("examining frame at {}".format(frameuri))

                o = urlparse(frameuri)

                timegate_stem = self.timegate[0:self.timegate.find(self.original_uri)]

                self.logger.debug("timegate stem is now {}".format(timegate_stem))

                # deal with relative URIs
                if o.netloc == '':

                    frameuri = urljoin(self.original_uri, frameuri)

                    if timegate_stem[-1] != '/':
                        urig = '/'.join([timegate_stem, frameuri])
                else:
                    urig = frameuri

                if urig is None:
                    urig = timegate_stem + frameuri
                    self.logger.debug("URI-G is now {}".format(urig))

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
                    module_logger.exception("failed to open document using BeautifulSoup")
                    raise MementoFramesParsingError(
                        "failed to open document using BeautifulSoup",
                        original_exception=e)

                framecontent = ""

                try:
                    for item in soup.findAll('body'):
                        for c in item.children:
                            # self.logger.debug("adding:\n{}".format(str(c)))
                            framecontent += str(c)

                except Exception as e:
                    module_logger.exception("failed to parse document using BeautifulSoup")
                    raise MementoFramesParsingError(
                        "failed to parse document using BeautifulSoup",
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

        try:
            frames = soup.findAll("frame")
        except Exception as e:
            module_logger.exception("failure while searching for frame tags in memento HTML")
            raise MementoFramesParsingError(
                "failure while searching for frame tags in memento HTML",
                original_exception=e
            )

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
                module_logger.exception("failed to open document using BeautifulSoup")
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
                module_logger.exception("failed to parse document using BeautifulSoup")
                raise MementoParsingError(
                    "failed to parse document using BeautifulSoup",
                    original_exception=e)

        else:

            bname = os.path.basename(self.urim)
            self.compressed_memento_urim = "http://archive.is/download/{}.zip".format(bname)

        self.logger.info("using compressed memento URI-M of {}".format(self.compressed_memento_urim))

        response = self.http_cache.get(self.compressed_memento_urim)

        try:
            z = zipfile.ZipFile(io.BytesIO(response.content))
            content = z.read('index.html')

            self.logger.debug("from Archive.is type of raw content: {}".format( type(content) ) )
            self.logger.debug("size of raw content: {}".format( len(content) ) )

        except zipfile.BadZipFile as e:
            module_logger.exception("zip file acquired from archive is malformed")
            # raise MementoParsingError(
            #     "zip file acquired from archive is malformed",
            #     original_exception=e)

            # for Archive.today's new behavior: no raw memento content
            soup = BeautifulSoup(self.content, "html5lib")
            content = "<html><body>{}</body></html>".format(soup.find(id='CONTENT').contents)

        return content


class IMFMemento(MementoResource):

    @property
    def raw_content(self):
        
        self.response = self.http_cache.get(self.urim)

        content = self.response.text

        try:
            soup = BeautifulSoup(content, "html5lib")
        except Exception as e:
            module_logger.exception("failed to open document using BeautifulSoup")
            raise MementoParsingError(
                "failed to open document using BeautifulSoup",
                original_exception=e)

        try:
            twp = soup.find("iframe", {"id": "theWebpage"})
        except Exception as e:
            module_logger.exception("failed to find iframe with id=theWebPage using BeautifulSoup")
            raise MementoParsingError(
                "failed to parse document using BeautifulSoup",
                original_exception=e)

        # TODO: create a function that returns the raw_urim without doing this request afterward
        self.raw_urim = twp.get('src')

        response = self.http_cache.get(self.raw_urim)

        return response.text


class WaybackMemento(MementoResource):

    def __init__(self, http_cache, urim, logger=None, given_uri=None):
        super(WaybackMemento, self).__init__(
            http_cache, urim, logger, given_uri
        )

        if 'archive.org/' in urim:
            # IA only does rewritten links on main URI-M
            self.im_urim = urim
        else:
            # we want rewritten links for image processing
            self.im_urim = wayback_pattern.sub(r'\1im_/', self.urim)

    @property
    def raw_content(self):

        try:
            soup = BeautifulSoup(self.response.text, 'html5lib')
        except Exception as e:
            module_logger.exception("failed to open document using BeautifulSoup")
            raise MementoParsingError(
                "failed to open document using BeautifulSoup",
                original_exception=e)

        try:
            frames = soup.findAll("frame")
        except Exception as e:
            module_logger.exception("failed to find frames using BeautifulSoup")
            raise MementoParsingError(
                "failed to parse document using BeautifulSoup",
                original_exception=e)

        if len(frames) > 0:

            framecontent = self.get_content_from_frames()
            return framecontent

        else:

            if len(self.response.history) == 0:
                self.raw_urim = wayback_pattern.sub(r'\1id_/', self.urim)
            else:
                self.raw_urim = wayback_pattern.sub(r'\1id_/', self.response.url)

            # self.raw_urim = wayback_pattern.sub(r'\1id_/', self.urim)
            self.logger.debug("using raw URI-M {}".format(self.raw_urim))
            raw_response = self.http_cache.get(self.raw_urim)
            return raw_response.text
