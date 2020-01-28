import re
import logging

import aiu
import requests

from urllib.parse import urlparse, urlunparse

from requests.exceptions import Timeout, TooManyRedirects, \
    ChunkedEncodingError, ContentDecodingError, StreamConsumedError, \
    URLRequired, MissingSchema, InvalidSchema, InvalidURL, \
    UnrewindableBodyError, ConnectionError, SSLError

from .archiveresource import archive_collection_patterns
from .mementoresource import get_original_uri_from_response, \
    get_memento_datetime_from_response, get_memento, \
    NotAMementoError

module_logger = logging.getLogger('mementoembed.seedresource')

def get_timemap_from_response(response):

    urit = None

    try:
        urit = response.links['timemap']['url']
    except KeyError as e:
        raise NotAMementoError(
            "link header could not be parsed for TimeMap URI",
            response=response, original_exception=e
        )

    return urit

class SeedResourceError(Exception):
    
    user_facing_error = "This is a problem processing the seed for this memento."

    def __init__(self, message, original_exception=None):
        self.message = message
        self.original_exception = original_exception

class InvalidTimeMapURI(SeedResourceError):

    user_facing_error = "The URI of the memento list (TimeMap) for this memento is invalid."

class TimeMapTimeoutError(SeedResourceError):

    user_facing_error = "Could not download a memento list (TimeMap) for this memento."

class TimeMapSSLError(SeedResourceError):

    user_facing_error = "There was a problem processing the certificate for the TimeMap for this memento."

class TimeMapConnectionFailure(SeedResourceError):

    user_facing_error = "Could not download a memento list (TimeMap) for this memento."


class SeedResource:

    def __init__(self, memento, httpcache):
        
        self.httpcache = httpcache
        self.memento = memento
        self.logger = logging.getLogger('mementoembed.seedresource.SeedResource')

        collection_id = None

        for pattern in archive_collection_patterns:

            self.logger.debug("attempting to match pattern {}".format(pattern))
            m = re.match(pattern, self.memento.urim)

            if m:
                self.logger.debug("matched pattern {}".format(m.group(1)))
                collection_id = m.group(1)
                break

        if collection_id is not None:

            self.aic = aiu.ArchiveItCollection(
                collection_id=collection_id,
                session=httpcache,
                logger=self.logger
            )

        else:
            self.aic = None

        self.logger.info("given URI: {}".format(self.memento.given_uri))
        self.logger.info("memento URI-M: {}".format(self.memento.urim))

        if self.memento.given_uri == self.memento.urim:

            response = get_memento(self.httpcache, memento.urim)

            self.logger.info("response history length: {}".format(len(response.history)))
            self.logger.debug("response headers: {}".format(response.headers))

            if len(response.history) == 0:
                self.urit = get_timemap_from_response(response)
                self.urir = get_original_uri_from_response(response)
            else:
                try:
                    self.urit = get_timemap_from_response(response.history[0])
                except NotAMementoError:
                    self.urit = get_timemap_from_response(response)

                try:
                    self.urir = get_original_uri_from_response(response.history[0])
                except NotAMementoError:
                    self.urir = get_original_uri_from_response(response)

        else:

            response = get_memento(self.httpcache, memento.given_uri)

            if len(response.history) == 0:
                self.urit = get_timemap_from_response(response)
                self.urir = get_original_uri_from_response(response)

            else:
                self.urit = get_timemap_from_response(response.history[0])
                self.urir = get_original_uri_from_response(response.history[0])

        self.sorted_mementos_list = []

    def fetch_timemap(self):

        try:
            # get URI-T
            r = self.httpcache.get(self.urit)
        
            self.timemap = aiu.convert_LinkTimeMap_to_dict(r.text)

            memento_list = []

            for memento in self.timemap["mementos"]["list"]:
                mdt = memento['datetime']
                urim = memento['uri']
                memento_list.append( (mdt, urim) )

            self.sorted_mementos_list = sorted(memento_list)

        except (URLRequired, MissingSchema, InvalidSchema, InvalidURL) as e:
            raise InvalidTimeMapURI("", original_exception=e)

        except Timeout as e:
            raise TimeMapTimeoutError("", original_exception=e)

        except SSLError as e:
            raise TimeMapSSLError("", original_exception=e)
            
        except (UnrewindableBodyError, ConnectionError) as e:
            raise TimeMapConnectionFailure("", original_exception=e)

    def mementocount(self):
        
        try:
            self.fetch_timemap()
            return len(self.timemap["mementos"]["list"])
        except aiu.timemap.MalformedLinkFormatTimeMap:
            return None

    def first_mdt(self):

        try:
            self.fetch_timemap()
            return self.sorted_mementos_list[0][0]
        except aiu.timemap.MalformedLinkFormatTimeMap:
            return None        

    def first_urim(self):

        try:
            self.fetch_timemap()
            return self.sorted_mementos_list[0][1]
        except aiu.timemap.MalformedLinkFormatTimeMap:
            return None        

    def last_mdt(self):

        try:
            self.fetch_timemap()
            return self.sorted_mementos_list[-1][0]
        except aiu.timemap.MalformedLinkFormatTimeMap:
            return None


    def last_urim(self):

        try:
            self.fetch_timemap()
            return self.sorted_mementos_list[-1][1]
        except aiu.timemap.MalformedLinkFormatTimeMap:
            return None

    def _develop_candidate_seed_uris(self):

        candidate_seed_uris = []

        candidate_seed_uris.append(self.urir)

        # replace http with https
        o = urlparse(self.urir)
        
        if o.scheme == 'http':
            onew = o._replace(scheme='https')
            candidate_seed_uris.append(urlunparse(onew))

        # replace https with http
        if o.scheme == 'https':
            onew = o._replace(scheme='https')
            candidate_seed_uris.append(urlunparse(onew))

        # remove slash from end
        if self.urir[-1] == '/':
            candidate_seed_uris.append(self.urir[:-1])
        else:
            # add slash to end
            candidate_seed_uris.append(self.urir + '/')

        # remove www to domain
        if o.netloc[0:3] == 'www':
            onew = o._replace(netloc=o.netloc[4:])
            candidate_seed_uris.append(urlunparse(onew))
        else:
            # insert www into domain
            onew = o._replace(netloc='www.' + o.netloc)
            candidate_seed_uris.append(urlunparse(onew))

        return candidate_seed_uris

    def seed_metadata(self):
        
        metadata = {}

        if self.aic is not None:

            self.aic.load_seed_metadata() # workaround for aiu bug

            self.logger.info("acquiring seed metadata for seed {}".format(self.urir))

            candidate_seed_uris = self._develop_candidate_seed_uris()

            for urir in candidate_seed_uris:

                try:
                    metadata = self.aic.get_seed_metadata(urir)['collection_web_pages']
                    return metadata

                except KeyError:
                    self.logger.exception("failed to match seed in collection, trying alternative candidate urir")

        return metadata
