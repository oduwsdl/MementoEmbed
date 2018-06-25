import logging

from urllib.parse import urljoin, urlparse

from tldextract import extract
from memento_client import MementoClient

from .favicon import get_favicon_from_google_service, get_favicon_from_html, \
    find_conventional_favicon_on_live_web, query_timegate_for_favicon, \
    get_favicon_from_resource_content, construct_conventional_favicon_uri

class OriginalResource:

    def __init__(self, memento, http_cache, logger=None):
        self.memento = memento
        self.http_cache = http_cache
        
        self.urim = self.memento.urim
        self.content = self.memento.content
        self.rawcontent = self.memento.raw_content

        self.original_link_favicon_uri = None

        self.logger = logger or logging.getLogger(__name__)

    @property
    def domain(self):
        # return extract(self.uri).registered_domain
        o = urlparse(self.uri)

        print("original domain parse: {}".format(o))

        return o.netloc.split(':')[0]
        
    @property
    def uri(self):
        return self.memento.original_uri

    @property
    def favicon(self):
        
        o = urlparse(self.uri)
        original_scheme = o.scheme

        # 1. try the HTML within the memento for a favicon, then query a TimeGate
        if self.original_link_favicon_uri is None:
            self.logger.info("interrogating HTML of memento for favicon URI")

            candidate_favicon = get_favicon_from_html(self.content)

            if candidate_favicon is not None:

                self.original_link_favicon_uri = query_timegate_for_favicon(
                    self.memento.timegate[0:self.memento.timegate.find(self.uri)],
                    candidate_favicon,
                    self.memento.memento_datetime,
                    self.http_cache
                )

        self.logger.info("failed to find favicon in HTML for URI {}".format(self.uri))

        # 2. try to construct the favicon URI and look for it in the archive
        if self.original_link_favicon_uri is None:
            self.logger.info("querying web archive for original favicon at conventional URI")

            self.original_link_favicon_uri = query_timegate_for_favicon(
                self.memento.timegate[0:self.memento.timegate.find(self.uri)],
                construct_conventional_favicon_uri(original_scheme, self.domain),
                self.memento.memento_datetime,
                self.http_cache   
            )

        self.logger.info("failed to find favicon in archive for URI {}".format(self.uri))

        # 3. request the home page of the site on the live web and look for favicon in its HTML
        if self.original_link_favicon_uri is None:

            self.logger.info("interrogating HTML of live web home page for favicon URI")

            self.original_link_favicon_uri = get_favicon_from_resource_content(
                "{}://{}".format(original_scheme, self.domain), self.http_cache)

        self.logger.info("failed to find favicon in HTML of live page for URI {}".format(self.uri))

        # 4. try to construct the favicon URI and look for it on the live web
        if self.original_link_favicon_uri is None:

            self.logger.info("requesting the live web home page of the resource and searching "
                "for the favicon in its content")

            self.original_link_favicon_uri = find_conventional_favicon_on_live_web(
                original_scheme, self.domain, self.http_cache)

        self.logger.info("failed to find favicon on live web for URI {}".format(self.uri))
        
        # 5. if all else fails, fall back to the Google favicon service
        if self.original_link_favicon_uri is None:

            self.logger.debug("attempting to query the google favicon service for the archive favicon URI")

            self.original_link_favicon_uri = get_favicon_from_google_service(
                self.http_cache, self.uri)

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

        