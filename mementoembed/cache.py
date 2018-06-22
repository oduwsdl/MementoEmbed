import concurrent.futures

import redis
import requests

from requests.exceptions import ConnectionError, TooManyRedirects

from .version import __useragent__

redis_expiration = 7 * 24 * 60 * 60

"""
These classes largely exist because I could not get the existing 
cachecontrol library to reliably cache responses.
"""

class MementoSurrogateCacheConnectionFailure(Exception):
    pass

def get_http_response_from_cache_model(cache_model, uri, session=requests.session()):
    """
        Function for checking the cache for a uri response object.

        The object in `cache_model` must support the method `get`
        retrieving items, and `set` for inserting items.
    """

    response = cache_model.get(uri)
    
    if response is None:

        try:

            response = session.get(uri)
            cache_model.set(uri, response)

        except ConnectionError:
            raise MementoSurrogateCacheConnectionFailure("Connection error for URI {}".format(uri))
        
        except TooManyRedirects:
            raise MementoSurrogateCacheConnectionFailure("Too many redirects encountered for URI {}".format(uri))

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
            except MementoSurrogateCacheConnectionFailure as e:
                # TODO: log this
                errors[uri] = e
            else:
                responses[uri] = response

    return responses, errors

class HTTPCache:

    def __init__(self, cache_model, session):
        """
        This constructor establishes an HTTP cache with
        `cache_model` as the object that stores the cache.

        The object in `cache_model` must support the method `get`
        retrieving items, and `set` for inserting items.
        """

        self.cache_model = cache_model
        self.session = session

    def get(self, uri):
        return get_http_response_from_cache_model(self.cache_model, uri, session=self.session)

    def is_uri_good(self, uri):
        pass

    def get_multiple(self, urilist):
        return get_multiple_http_responses_from_cache_model(self.cache_model, urilist, session=self.session)

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
        return self.rconn.get(key)

    def set(self, key, value):
        """
            Set a key in the redis database.
            The key expires after `redis_expiration` seconds.
        """
        self.rconn.set(key)
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
