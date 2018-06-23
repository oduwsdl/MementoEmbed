import logging

from urllib.parse import urljoin, urlparse

from tldextract import extract
from memento_client import MementoClient

from .favicon import get_favicon_from_google_service, get_favicon_from_html

class OriginalResource:

    def __init__(self, memento, http_cache, logger=None):
        self.memento = memento
        self.http_cache = http_cache
        
        self.urim = self.memento.urim
        self.content = self.memento.content

        self.original_link_favicon_uri = None

        self.logger = logger or logging.getLogger(__name__)

    @property
    def domain(self):
        return extract(self.uri).registered_domain
        
    @property
    def uri(self):
        return self.memento.original_uri

    @property
    def favicon(self):
        
        o = urlparse(self.uri)
        original_scheme = o.scheme

        # 1. try the HTML within the memento for a favicon
        if self.original_link_favicon_uri is None:
            self.logger.info("interrogating HTML of memento for favicon URI")

            self.original_link_favicon_uri = get_favicon_from_html(self.content)

            if self.original_link_favicon_uri:

                if self.original_link_favicon_uri[0:4] != 'http':
                    # in this case we have a relative link
                    self.original_link_favicon_uri = urljoin(self.urim, self.original_link_favicon_uri)

                # TODO: what if the favicon discovered this way is not a memento? - we use datetime negotiation
                self.logger.debug("using favicon discovered by interrogating HTML: {}".format(self.original_link_favicon_uri))

                if not self.http_cache.is_uri_good(self.original_link_favicon_uri):
                    self.original_link_favicon_uri = None

        # 2. try to construct the favicon URI and look for it in the archive
        candidate_favicon_uri = "{}://{}/favicon.ico".format(
                original_scheme, self.domain)

        if self.original_link_favicon_uri == None:
            self.logger.info("querying web archive for original favicon at conventional URI")

            favicon_timegate = "{}/{}".format(
                self.memento.timegate[0:self.memento.timegate.find(self.uri)],
                candidate_favicon_uri)

            self.logger.debug("using URI-G of {}".format(favicon_timegate))

            mc = MementoClient(timegate_uri=favicon_timegate, check_native_timegate=False)

            try:
                memento_info = mc.get_memento_info(candidate_favicon_uri, 
                    self.memento.memento_datetime,
                    session=self.http_cache)

                self.logger.debug("got back memento_info of {}".format(memento_info))

                if "mementos" in memento_info:

                    if "closest" in memento_info["mementos"]:

                        if "uri" in memento_info["mementos"]["closest"]:
                            candidate_memento_favicon_uri = memento_info["mementos"]["closest"]["uri"][0]

                            r = self.http_cache.get(self.original_link_favicon_uri)

                            if r.status_code == 200:

                                if 'image/' in r.headers['content-type']:

                                    self.logger.debug("using favicon discovered through datetime negotiation: {}".format(candidate_memento_favicon_uri))
                                    self.original_link_favicon_uri = candidate_memento_favicon_uri

            except Exception as e:
                # it appears that MementoClient throws 
                self.logger.info("got an exception while searching for the original favicon at {}: {}".format(candidate_favicon_uri, repr(e)))
                self.original_link_favicon_uri = None

        # 3. request the home page of the site on the live web and look for favicon in its HTML
        if self.original_link_favicon_uri == None:
            live_site_uri = "{}://{}".format(original_scheme, self.domain)

            r = self.http_cache.get(live_site_uri)

            candidate_favicon_uri_from_live = get_favicon_from_html(r.text)

            if candidate_favicon_uri_from_live:

                if candidate_favicon_uri_from_live[0:4] != 'http':
                    self.original_link_favicon_uri = urljoin(live_site_uri, candidate_favicon_uri_from_live)

                if not self.http_cache.is_uri_good(self.original_link_favicon_uri):
                    self.original_link_favicon_uri = None

        # 4. try to construct the favicon URI and look for it on the live web
        if self.original_link_favicon_uri == None:

            r = self.http_cache.get(candidate_favicon_uri)

            if r.status_code == 200:

                # this is some protection against soft-404s
                if 'image/' in r.headers['content-type']:
                    self.original_link_favicon_uri = candidate_favicon_uri

                if not self.http_cache.is_uri_good(self.original_link_favicon_uri):
                    self.original_link_favicon_uri = None
        
        # 5. if all else fails, fall back to the Google favicon service
        if self.original_link_favicon_uri == None:

            self.original_link_favicon_uri = get_favicon_from_google_service(self.http_cache, self.uri)

            if not self.http_cache.is_uri_good(self.original_link_favicon_uri):
                self.original_link_favicon_uri = None

        self.logger.debug("discovered memento favicon at {}".format(self.original_link_favicon_uri))

        return self.original_link_favicon_uri

    @property
    def link_status(self):
        
        status = None

        try:

            response = self.http_cache.get(self.uri)

            if response.status_code == 200:
                status = "Live"
            else:
                status = "Rotten"
    
        except Exception:
            # TODO: make this exception more explicit
            status = "Rotten"

        return status

        