import logging

import requests
import brotli
import requests_cache

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


class ManagedSession:

    def __init__(self, timeout, user_agent, starting_uri, session=None):

        self.timeout = float(timeout)
        self.starting_uri = starting_uri
        self.user_agent = user_agent
        
        if session is None:
            self.session = session
        else:
            self.session = requests.Session()

        self.session.headers.update( {'User-Agent': user_agent} )

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

        response = self.session.get(uri, headers=req_headers, timeout=self.timeout)

        module_logger.debug("request headers sent were {}".format(response.request.headers))
        module_logger.debug("response status: {}".format(response.status_code))
        module_logger.debug("response headers: {}".format(response.headers))

        if 'content-encoding' in response.headers:
            if response.headers['content-encoding'] == 'br':
                response = BrotliResponse(response)

        return response
