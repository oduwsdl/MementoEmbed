import pickle
import concurrent.futures
import logging

import redis
import requests

from requests.exceptions import RequestException

from .version import __useragent__

redis_expiration = 7 * 24 * 60 * 60

"""
These classes largely exist because I could not get the existing 
cachecontrol library to reliably cache responses.
"""

class MementoSurrogateCacheConnectionFailure(Exception):
    pass

def get_http_response_from_cache_model(cache_model, uri, session=requests.session(), headers=None):
    """
        Function for checking the cache for a uri response object.

        The object in `cache_model` must support the method `get`
        retrieving items, and `set` for inserting items.
    """

    response = cache_model.get(uri)
    
    if response is None:

        req_headers = {
            'user-agent': __useragent__
        }

        if headers is not None:

            for key in headers:
                req_headers[key] = headers[key]

        response = session.get(uri, headers=req_headers)

        try:
            #pylint: disable=unused-variable
            mdt = response.headers['memento-datetime']
            cache_model.set(uri, response)
        except KeyError:
            # only cache 200 responses for non-mementos
            if response.status_code == 200:
                cache_model.set(uri, response)

    return response

def get_multiple_http_responses_from_cache_model(cache_model, urilist, session=requests.session()):
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:

        responses = {}
        errors = {}

        futures = { executor.submit(get_http_response_from_cache_model, cache_model, uri, session): uri for uri in urilist }

        for future in concurrent.futures.as_completed(futures):

            uri = futures[future]

            try:
                response = future.result()
            except RequestException as e:
                # TODO: log this
                errors[uri] = e
            else:
                responses[uri] = response

    return responses, errors

class HTTPCache:

    def __init__(self, cache_model, session, logger=None):
        """
        This constructor establishes an HTTP cache with
        `cache_model` as the object that stores the cache.

        The object in `cache_model` must support the method `get`
        retrieving items, and `set` for inserting items.
        """

        self.cache_model = cache_model
        self.session = session

        self.logger = logger or logging.getLogger(__name__)

    def get(self, uri, headers=None):

        self.logger.debug("searching cache before requesting URI {}".format(uri))
        
        response = get_http_response_from_cache_model(self.cache_model, uri, session=self.session, headers=headers)

        return response

    def get_multiple(self, urilist):
        # TODO: log failures
        return get_multiple_http_responses_from_cache_model(self.cache_model, urilist, session=self.session)

    def head(self, uri):
        # TODO: log failures
        return get_http_response_from_cache_model(self.cache_model, uri, session=self.session)

    def close(self):
        self.session.close()

class RedisCacheModel:
    """
        A cache model that uses the redis database.
    """

    def __init__(self, db=0, host="localhost", port=6379, rconn=None):
        """
            Construct the RedisCacheModel. If `rconn` is supplied 
            as an existing redis connection, then it will be used.
            Otherwise a new Redis connection will be created based
            on the values of `db`, `host`, and `port`.
        """

        if rconn is None:
            pool = redis.ConnectionPool(host=host, port=port, db=db)
            self.rconn = redis.Redis(connection_pool=pool)
        else:
            self.rconn = rconn

    def get(self, key):
        """
            Get the value of `key` from the Redis database.
        """
        
        try:
            value = pickle.loads(self.rconn.get(key))
        except TypeError:
            value = self.rconn.get(key)
        
        return value

    def set(self, key, value):
        """
            Set a key in the redis database.
            The key expires after `redis_expiration` seconds.
        """

        if type(value) != str:
            value = pickle.dumps(value)

        self.rconn.set(key, value)
        self.rconn.expire(key, redis_expiration)

class DictCacheModel:
    """
        A cache model that uses an in-memory Python dictionary.
    """

    def __init__(self):
        self.dictcache = {}

    def get(self, key):
        if key in self.dictcache:
            return self.dictcache[key]
        else:
            return None

    def set(self, key, value):
        self.dictcache[key] = value
