from datetime import datetime

from .mementoresource import raw_content_factory
from .originalresource import OriginalResource
from .imageselection import get_best_image
from .archiveresource import ArchiveResource
from .textprocessing import extract_text_snippet, extract_title

class MementoSurrogate:
    """
        Surrogate provides a single interface to
        all information about surrogates
        related to content, uri, and response_headers.
    """
    def __init__(self, urim, httpcache, working_directory="/tmp/mementosurrogate", logger=None):

        self.surrogate_creation_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.urim = urim
        self.httpcache = httpcache
        self.logger = logger

        self.memento = raw_content_factory(self.urim, self.httpcache)

        self.originalresource = OriginalResource(self.memento, self.httpcache)

        self.archive = ArchiveResource(self.urim, self.httpcache, working_directory, logger=self.logger)

    @property
    def creation_time(self):
        return self.surrogate_creation_time

    @property
    def text_snippet(self):
        return extract_text_snippet(self.memento.raw_content)

    @property
    def title(self):
        return extract_title(self.memento.raw_content)

    @property
    def memento_datetime(self):
        return self.memento.memento_datetime

    @property
    def striking_image(self):
        return get_best_image(self.memento.content)

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
        return self.archive.uri

    @property
    def archive_name(self):
        return self.archive.name

    @property
    def archive_favicon(self):
        return self.archive.favicon

    @property
    def archive_collection_id(self):
        return self.archive.collection_id

    @property
    def archive_collection_name(self):
        return self.archive.collection_name

    @property
    def archive_collection_uri(self):
        return self.archive.collection_uri