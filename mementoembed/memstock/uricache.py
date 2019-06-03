import json
import logging
import datetime

from redis_namespace import StrictRedis
import requests
from requests.models import Response
from requests.structures import CaseInsensitiveDict

module_logger = logging.getLogger('mementoembed.memstock.uricache')

# this whole implementation exists because requests_cache
# would occasionally return incorrect content for a URI
# and I could not determine why

# timeout
# retries

class URICacheError(Exception):
    pass

class URINotInCacheError(URICacheError):
    pass

class URICache:

    def __init__(self, credentials, session, expiration_delta):
        self.credentials = credentials
        self.session = session
        self.expiration_delta = expiration_delta

class RedisCache(URICache):

    def __init__(self, credentials, session, expiration_delta):

        module_logger.debug("setting up Redis cache at with credentials {}".format(credentials))

        self.conn = StrictRedis(
            host=credentials['host'],
            port=credentials['port'],
            password=credentials['password'],
            db=credentials['dbnumber'],
            namespace='uricache:'
        )

        module_logger.debug("Redis cache set up with object {}".format(self.conn))

        self.session = session
        self.expiration_delta = int(expiration_delta)

    def purgeuri(self, uri):
        module_logger.debug("purging URI {}".format(uri))
        self.conn.delete(uri)

    def saveuri(self, uri):

        module_logger.debug("saving URI to cache: {}".format(uri))

        r = self.session.get(uri)

        observation_datetime = datetime.datetime.utcnow()

        self.conn.hset(uri, "request_headers", json.dumps(dict(r.request.headers)))
        self.conn.hset(uri, "request_method", r.request.method)
        self.conn.hset(uri, "response_status", r.status_code)
        self.conn.hset(uri, "response_reason", r.reason)
        self.conn.hset(uri, "response_elapsed", r.elapsed.microseconds)
        self.conn.hset(uri, "response_headers", json.dumps(dict(r.headers)))

        # sometimes there is no encoding
        if r.encoding is not None:
            self.conn.hset(uri, "response_encoding", r.encoding)

        self.conn.hset(uri, "response_content", r.content)
        self.conn.hset(uri, "observation_datetime", observation_datetime.strftime("%Y-%m-%dT%H:%M:%S"))

        module_logger.debug("URI {} should now be written to the cache {}".format(
            uri, self.conn))

    def get(self, uri, headers={}, timeout=None):

        observation_datetime = self.conn.hget(uri, "observation_datetime")

        if observation_datetime is not None:

            odt = datetime.datetime.strptime(observation_datetime.decode('utf-8'), "%Y-%m-%dT%H:%M:%S")
            module_logger.debug("expiring URI if it more than {} seconds old".format(self.expiration_delta))

            age = (datetime.datetime.utcnow() - odt).seconds
            module_logger.debug("URI is {} - {} = {} seconds old".format(datetime.datetime.utcnow(), odt, age))

            if age > self.expiration_delta:
                self.purgeuri(uri)

        if self.conn.hget(uri, "response_status") is None:
            self.saveuri(uri)

        req_headers = CaseInsensitiveDict(json.loads(self.conn.hget(uri, "request_headers")))
        req_method = self.conn.hget(uri, "request_method")
        request = requests.Request(req_method, uri, headers=req_headers)
        request.prepare()

        response = Response()
        response.request = request
        response.status_code = int(self.conn.hget(uri, "response_status"))
        response.reason = self.conn.hget(uri, "response_reason")
        response.elapsed = datetime.timedelta(microseconds=int(self.conn.hget(uri, "response_elapsed")))
        
        if type(self.conn.hget(uri, "response_encoding")) is bytes:
            response.encoding = self.conn.hget(uri, "response_encoding").decode('utf-8')
        else:
            response.encoding = self.conn.hget(uri, "response_encoding")
        

        module_logger.debug("encoding set to {} for URI {}".format(response.encoding, uri))
        response.headers = CaseInsensitiveDict(json.loads(self.conn.hget(uri, "response_headers")))
        response._content = self.conn.hget(uri, "response_content")
        response.url = uri

        return response

class NoCache(URICache):

    def __init__(self, credentials, session, expiration_delta):

        self.session = session
    
    def purgeuri(self, uri):

        # We purge NOTHING! NO PURGE FOR YOU!
        pass

    def get(self, uri, headers={}, timeout=None):

        return self.session.get(uri)
