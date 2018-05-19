from .mementoembed import app
from .surrogate import Surrogate
from .archiveinfo import identify_archive, identify_collection, \
    get_archive_favicon, archive_names, get_collection_uri, \
    get_archive_uri

__all__ = [
    "Surrogate", "identify_archive", 
    "identify_collection", "get_archive_favicon",
    "archive_names", "get_collection_uri",
    "get_archive_uri"
    ]