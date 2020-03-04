import logging

from datetime import datetime

from .mementoresource import memento_resource_factory
from .originalresource import OriginalResource
from .imageselection import get_best_image
from .archiveresource import ArchiveResource
from .textprocessing import extract_text_snippet, extract_title, TitleExtractionError

module_logger = logging.getLogger('mementoembed.mementosurrogate')

class MementoSurrogate:
    """
        Surrogate provides a single interface to
        all information about surrogates
        related to content, uri, and response_headers.
    """
    def __init__(self, urim, httpcache, working_directory="/tmp/mementosurrogate", default_image_uri=None):

        self.surrogate_creation_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.urim = urim
        self.httpcache = httpcache
        self.logger = logging.getLogger('mementoembed.mementosurrogate.MementoSurrogate')

        self.memento = memento_resource_factory(self.urim, self.httpcache)

        self.originalresource = OriginalResource(self.memento, self.httpcache)

        self.archive = ArchiveResource(self.urim, self.httpcache)

        self.default_image_uri = default_image_uri

    @property
    def creation_time(self):
        return self.surrogate_creation_time

    @property
    def text_snippet(self):
        raw_content = self.memento.raw_content

        self.logger.debug("extracting text from raw content, currently size {}".format(len(raw_content)))

        return extract_text_snippet(raw_content)

    @property
    def title(self):
        try:
            pagetitle = extract_title(self.memento.raw_content)
        except TitleExtractionError:
            self.logger.exception("failed to extract title from content for {}, attempting with non-raw content".format(self.urim))
            pagetitle = extract_title(self.memento.content)

        return pagetitle

    @property
    def memento_datetime(self):
        return self.memento.memento_datetime

    @property
    def striking_image(self):
        self.logger.info("looking for the best image in the memento")
        return get_best_image(self.memento.im_urim, self.httpcache, default_image_uri=self.default_image_uri)

    @property
    def original_uri(self):
        return self.originalresource.uri

    @property
    def original_domain(self):
        return self.originalresource.domain

    @property
    def original_link_status(self):
        return self.originalresource.link_status

    @property
    def original_favicon(self):
        return self.originalresource.favicon

    @property
    def archive_uri(self):
        return self.archive.home_uri

    @property
    def archive_name(self):
        return self.archive.name

    @property
    def archive_favicon(self):
        return self.archive.favicon

    @property
    def collection_id(self):
        return self.archive.collection_id

    @property
    def collection_name(self):
        return self.archive.collection_name

    @property
    def collection_uri(self):
        return self.archive.collection_uri
