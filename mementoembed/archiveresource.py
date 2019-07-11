import re
import logging
# import inspect

import requests
import tldextract
import aiu
from bs4 import BeautifulSoup

from urllib.parse import urlparse, urljoin

from .favicon import get_favicon_from_google_service, \
    get_favicon_from_html, find_conventional_favicon_on_live_web, \
    favicon_resource_test

module_logger = logging.getLogger('mementoembed.archiveresource')

archive_collection_patterns = [
    "http://wayback.archive-it.org/([0-9]*)/[0-9]{14}/.*",
    "https://wayback.archive-it.org/([0-9]*)/[0-9]{14}/.*",
    "https://webrecorder.io/([^/]+)/([^/]*)/.*"
]

archive_collection_uri_prefixes = {
    "archive-it.org": "https://archive-it.org/collections/{}",
    "webrecorder.io": "https://webrecorder.io/{}/{}"
}

home_uri_list = {
    "archive-it.org": "https://archive-it.org",
    "archive.org": "https://archive.org"
}

class ArchiveResource:

    def __init__(self, urim, httpcache):

        self.urim = urim
        self.logger = logging.getLogger('mementoembed.archiveresource.ArchiveResource')

        self.httpcache = httpcache

        self.memento_archive_name = None
        self.memento_archive_domain = None
        self.memento_archive_scheme = None
        self.memento_archive_uri = None
        self.archive_favicon_uri = None

        self.archive_collection_uri = None
        self.archive_collection_id = None
        self.archive_collection_name = None
        self.archive_collection_user = None

        # TODO: some kind of archive information cache

    @property
    def scheme(self):
        """
            Derives the scheme of the memento's archive URI.
        """

        if self.memento_archive_scheme == None:

            o = urlparse(self.urim)
            self.memento_archive_scheme = o.scheme

        return self.memento_archive_scheme

    @property
    def domain(self):
        """
            Derives the domain of the memento's archive URI.
        """

        if self.memento_archive_domain == None:
            # self.memento_archive_domain = tldextract.extract(self.uri).registered_domain
            o = urlparse(self.uri)
            self.memento_archive_domain = o.netloc

        return self.memento_archive_domain

    @property
    def registered_domain(self):
        return tldextract.extract(self.uri).registered_domain

    @property
    def home_uri(self):

        home_uri = self.uri

        if self.registered_domain in home_uri_list:
            home_uri = home_uri_list[self.registered_domain]

        return home_uri

    @property
    def name(self):

        if self.memento_archive_name == None:

            self.memento_archive_name = self.registered_domain.upper()
        
        return self.memento_archive_name

    @property
    def favicon(self):

        # a workaround for Archive-It's redirection behavior on playback
        if self.name == 'ARCHIVE-IT.ORG':
            return "https://www.archive-it.org/favicon.ico"

        # self.logger.debug("call stack: {}".format( inspect.stack() ))

        self.logger.debug("archive favicon uri: {}".format(self.archive_favicon_uri))

        # 1 try the HTML within the archive's web page for a favicon
        if self.archive_favicon_uri is None:
            
            self.logger.debug("attempting to acquire the archive favicon URI from HTML at {}".format(self.uri))

            r = self.httpcache.get(self.uri, use_referrer=False)

            # self.logger.debug("searching through HTML: \n\n{}\n\n".format(r.text))

            # self.logger.debug("searching through content: \n\n{}\n\n".format(r.content.decode('utf8')))

            candidate_favicon = get_favicon_from_html(r.text)

            self.logger.debug("retrieved archive candidate favicon: {}".format(candidate_favicon))

            self.archive_favicon_uri = urljoin(self.uri, candidate_favicon)

            self.logger.debug("got an archive favicon of {}".format(self.archive_favicon_uri))

            r = self.httpcache.get(self.archive_favicon_uri, use_referrer=False)

            if not favicon_resource_test(r):
                self.archive_favicon_uri = None

        self.logger.debug("archive favicon after step 1: {}".format(self.archive_favicon_uri))

        # 2. try to construct the favicon URI and look for it on the live web
        if self.archive_favicon_uri is None:

            self.logger.debug("attempting to use the conventional favicon URI to find the archive favicon URI")

            self.archive_favicon_uri = find_conventional_favicon_on_live_web(self.scheme, self.domain, self.httpcache)

        self.logger.debug("archive favicon after step 2: {}".format(self.archive_favicon_uri))

        # 3. if all else fails, fall back to the Google favicon service
        if self.archive_favicon_uri is None:

            self.logger.debug("attempting to query the google favicon service for the archive favicon URI")

            self.archive_favicon_uri = get_favicon_from_google_service(
                self.httpcache, self.uri)

        self.logger.debug("discovered archive favicon at {}".format(self.archive_favicon_uri))

        self.logger.debug("archive favicon after step 3: {}".format(self.archive_favicon_uri))

        return self.archive_favicon_uri

    @property
    def uri(self):

        if self.memento_archive_uri == None:
            o = urlparse(self.urim)
            # domain = tldextract.extract(self.urim).registered_domain

            self.memento_archive_uri = "{}://{}".format(o.scheme, o.netloc)

        return self.memento_archive_uri

    @property
    def collection_name(self):

        if self.archive_collection_name == None:

            if self.collection_id:

                if 'archive-it.org' in self.urim:

                    aic = aiu.ArchiveItCollection(
                        collection_id=self.collection_id,
                        session=self.httpcache,
                        logger=self.logger
                        )

                    self.archive_collection_name = aic.get_collection_name()

                elif 'webrecorder.io' in self.urim:

                    foundname = False

                    try:
                        r = self.httpcache.get(self.collection_uri)

                        if r.status_code == 200:
                            soup = BeautifulSoup(r.content, 'html5lib')
                            divs = soup.find_all("div", { "class": "capstone-column"} )

                            self.archive_collection_name = divs[0].find_all('h3')[0].get_text()
                            foundname = True

                    except Exception:
                        module_logger.exception("Something went wrong while trying to find a Webrecorder collection name.")

                    if foundname is False:
                        module_logger.warning("Falling back to guessing WR colleciton name with default text replacement.")
                        self.archive_collection_name = self.collection_id.replace('-', ' ').title()

        return self.archive_collection_name

    @property
    def collection_id(self):

        self.logger.debug("collection ID is {}".format(self.archive_collection_id))

        if self.archive_collection_id == None:

            for pattern in archive_collection_patterns:

                self.logger.debug("attempting to match pattern {}".format(pattern))
                m = re.match(pattern, self.urim)

                if m is not None:

                    if len(m.groups()) == 1:
                        self.logger.debug("matched pattern {}".format(m.group(1)))
                        self.archive_collection_id = m.group(1)
                        break
                    elif len(m.groups()) == 2:
                        self.logger.debug("matched patterns {} and {}".format(m.group(1), m.group(2)))
                        self.archive_collection_user = m.group(1)
                        self.archive_collection_id = m.group(2)

            self.logger.debug("discovered collection identifier {}".format(self.archive_collection_id))

        return self.archive_collection_id

    @property
    def collection_uri(self):

        if self.archive_collection_uri == None:

            if self.collection_id:

                try:
                    if self.archive_collection_user is None:
                        self.archive_collection_uri = archive_collection_uri_prefixes[self.registered_domain].format(
                            self.collection_id)
                    else:
                        self.archive_collection_uri = archive_collection_uri_prefixes[self.registered_domain].format(
                            self.archive_collection_user, self.collection_id)
                except KeyError:
                    self.archive_collection_uri = None

        return self.archive_collection_uri
