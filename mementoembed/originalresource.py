import logging
from requests.exceptions import ReadTimeout

from urllib.parse import urljoin, urlparse

from tldextract import extract

from .favicon import get_favicon_from_google_service, get_favicon_from_html, \
    find_conventional_favicon_on_live_web, query_timegate_for_favicon, \
    get_favicon_from_resource_content, construct_conventional_favicon_uri

from .mementoresource import get_memento_datetime_from_response, NotAMementoError, \
    MementoURINotAtArchiveFailure

module_logger = logging.getLogger('mementoembed.originalresource')

class OriginalResource:

    def __init__(self, memento, http_cache):
        self.memento = memento
        self.http_cache = http_cache
        
        self.urim = self.memento.urim
        self.content = self.memento.content
        self.rawcontent = self.memento.raw_content

        self.original_link_favicon_uri = None

        self.logger = logging.getLogger('mementoembed.originalresource.OriginalResource')

    @property
    def domain(self):
        # return extract(self.uri).registered_domain
        o = urlparse(self.uri)

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

            self.logger.debug("interrogating HTML of memento for favicon URI")

            candidate_favicon = get_favicon_from_html(self.content)

            self.logger.debug("retrieved candidate favicon of {}".format(candidate_favicon))

            if candidate_favicon is not None:

                try:
                    candidate_favicon = urljoin(self.urim, candidate_favicon)
                    r = self.http_cache.get(candidate_favicon)
                    get_memento_datetime_from_response(r)

                    if r.status_code == 200:
                        # if we get here, then it is a memento, just use it
                        self.original_link_favicon_uri = candidate_favicon

                except (NotAMementoError, MementoURINotAtArchiveFailure):
                    # try datetime negotiation
                    self.original_link_favicon_uri = query_timegate_for_favicon(
                        self.memento.timegate[0:self.memento.timegate.find(self.uri)],
                        candidate_favicon,
                        self.memento.memento_datetime,
                        self.http_cache
                    )
                
                except ReadTimeout:
                    module_logger.exception("Failed to download favicon due to timeout error, searching for favicon using a different method...")
                
                self.logger.debug("original link favicon after #1 is now {}".format(self.original_link_favicon_uri))

        # 2. try to construct the favicon URI and look for it in the archive
        if self.original_link_favicon_uri is None:

            self.logger.debug("failed to find favicon in HTML for URI {}".format(self.uri))
            self.logger.debug("querying web archive for original favicon at conventional URI")

            self.original_link_favicon_uri = query_timegate_for_favicon(
                self.memento.timegate[0:self.memento.timegate.find(self.uri)],
                construct_conventional_favicon_uri(original_scheme, self.domain),
                self.memento.memento_datetime,
                self.http_cache   
            )

            self.logger.debug("original link favicon after #2 is now {}".format(self.original_link_favicon_uri))

        # 3. request the home page of the site on the live web and look for favicon in its HTML
        if self.original_link_favicon_uri is None:

            self.logger.debug("failed to find favicon in archive for URI {}".format(self.uri))
            self.logger.debug("interrogating HTML of live web home page for favicon URI")

            self.original_link_favicon_uri = get_favicon_from_resource_content(
                "{}://{}".format(original_scheme, self.domain), self.http_cache)

            self.logger.debug("original link favicon after #3 is now {}".format(self.original_link_favicon_uri))

        # 4. try to construct the favicon URI and look for it on the live web
        if self.original_link_favicon_uri is None:

            self.logger.debug("failed to find favicon in HTML of live page for URI {}".format(self.uri))
            self.logger.debug("requesting the live web home page of the resource and searching "
                "for the favicon in its content")

            self.original_link_favicon_uri = find_conventional_favicon_on_live_web(
                original_scheme, self.domain, self.http_cache)

            self.logger.debug("original link favicon after #4 is now {}".format(self.original_link_favicon_uri))

        # 5. if all else fails, fall back to the Google favicon service
        if self.original_link_favicon_uri is None:

            self.logger.debug("failed to find favicon on live web for URI {}".format(self.uri))
            self.logger.debug("attempting to query the google favicon service for the archive favicon URI")

            self.original_link_favicon_uri = get_favicon_from_google_service(
                self.http_cache, self.uri)

            self.logger.debug("original link favicon after #5 is now {}".format(self.original_link_favicon_uri))

        self.logger.debug("discovered original link favicon at {}".format(self.original_link_favicon_uri))

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

        