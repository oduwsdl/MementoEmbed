import requests
import requests_cache

class CacheSession:

    def __init__(self, timeout, user_agent, starting_uri):

        self.timeout = float(timeout)
        self.starting_uri = starting_uri
        self.user_agent = user_agent

        self.session = requests.Session()
        self.session.headers.update( {'User-Agent': user_agent} )

    def get(self, uri, headers={}, use_referrer=True):

        req_headers = {}

        for key in headers:
            req_headers[key] = headers[key]

        if use_referrer:
            req_headers['Referer'] = self.starting_uri

        return self.session.get(uri, headers=req_headers, timeout=self.timeout)