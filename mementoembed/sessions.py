import logging

import requests
import brotli

from requests_cache import CachedSession

from .version import __useragent__

module_logger = logging.getLogger('mementoembed.sessions')   

class BrotliResponse:
    """
        This class exists because requests had not yet implemented the
        Brotli content-encoding ('br').
    """

    def __init__(self, response):
        self.response = response
        self._content = False
        self.apparent_encoding = self.response.apparent_encoding
        self.links = self.response.links
        self.headers = self.response.headers
        self.status_code = self.response.status_code
        self.url = self.response.url

    @property
    def content(self):

        if self._content is False:

            self._content = self.response.content

            if 'content-encoding' in self.response.headers:
                if self.response.headers['content-encoding'] == 'br':
                    self._content = brotli.decompress(self._content)

        return self._content

    @property
    def text(self):

        content = None
        encoding = self.response.encoding

        if self.response.encoding is None:
            encoding = self.apparent_encoding

        try:
            content = str(self.content, encoding, errors='replace')
        except (LookupError, TypeError):
            content = str(self.content, errors='replace')

        return content


class ManagedSession(CachedSession):

    def __init__(self, 
        cache_name='cache', backend=None, expire_after=None,
        allowable_codes=(200,), allowable_methods=('GET',),
        filter_fn=lambda r: True, old_data_on_error=False,
        timeout=300, user_agent=__useragent__, 
        starting_uri="", **backend_options
    ):

        self.timeout = float(timeout)
        self.starting_uri = starting_uri
        self.user_agent = user_agent
        # self.uricache = uricache

        super(ManagedSession, self).__init__(
            cache_name=cache_name,
            backend=backend,
            expire_after=expire_after,
            allowable_codes=allowable_codes,
            filter_fn=filter_fn,
            old_data_on_error=old_data_on_error,
            **backend_options
        )

    def get(self, uri, headers={}, use_referrer=True):

        req_headers = {}

        req_headers['accept-encoding'] = "gzip, deflate"

        module_logger.debug("requesting URI {}".format(uri))

        for key in headers:
            # Note that this will allow the caller to overwrite the accept-encoding
            req_headers[key] = headers[key]

        if use_referrer:
            if uri != self.starting_uri:
                req_headers['Referer'] = self.starting_uri

        req_headers['User-Agent'] = self.user_agent

        module_logger.debug("setting user agent to {} for URI {}".format(self.user_agent, uri))
        module_logger.debug("sending request with headers {} for URI {}".format(req_headers, uri))

        response = super(ManagedSession, self).get(uri, headers=req_headers, timeout=self.timeout)

        module_logger.debug("request headers sent were {} for URI {}".format(response.request.headers, uri))
        module_logger.debug("response status is {} for URI {}".format(response.status_code, uri))
        module_logger.debug("response headers are {} for URI {}".format(response.headers, uri))

        if 'content-encoding' in response.headers:
            if response.headers['content-encoding'] == 'br':
                response = BrotliResponse(response)

        return response
