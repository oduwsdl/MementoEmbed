import re
import logging

import aiu
import requests

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

        response = get_memento(self.httpcache, memento.urim)
        self.urit = get_timemap_from_response(response)
        self.urir = get_original_uri_from_response(response)

    def fetch_timemap(self):

        try:
            # get URI-T
            r = self.httpcache.get(self.urit)
        
            self.timemap = aiu.convert_LinkTimeMap_to_dict(r.text)

            # process and store TimeMap

        except (URLRequired, MissingSchema, InvalidSchema, InvalidURL) as e:
            raise InvalidTimeMapURI("", original_exception=e)

        except Timeout as e:
            raise TimeMapTimeoutError("", original_exception=e)

        except SSLError as e:
            raise TimeMapSSLError("", original_exception=e)
            
        except (UnrewindableBodyError, ConnectionError) as e:
            raise TimeMapConnectionFailure("", original_exception=e)

    def mementocount(self):
        
        self.fetch_timemap()

        return len(self.timemap["mementos"]["list"])

    def first_mdt(self):

        self.fetch_timemap()
        
        return self.timemap["mementos"]["first"]["datetime"]

    def first_urim(self):

        self.fetch_timemap()

        return self.timemap["mementos"]["first"]["uri"]

    def last_mdt(self):

        self.fetch_timemap()
        
        return self.timemap["mementos"]["last"]["datetime"]

    def last_urim(self):

        self.fetch_timemap()

        return self.timemap["mementos"]["last"]["uri"]

    def seed_metadata(self):
        
        metadata = {}

        if self.aic is not None:

            self.aic.load_seed_metadata() # workaround for aiu bug
            metadata = self.aic.get_seed_metadata(self.urir)['collection_web_pages']

        return metadata
