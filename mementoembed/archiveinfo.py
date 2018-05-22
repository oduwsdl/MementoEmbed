import re
import tldextract

archive_names = {
    "archive-it.org": "Archive-It",
    "archive.org": "Internet Archive",
    "webcitation.org": "WebCite",
    "archive.is": "archive.today"
}

archive_uris = {
    "Archive-It": "https://www.archive-it.org/",
    "Internet Archive": "https://archive.org",
    "WebCite": "http://webcitation.org",
    "archive.today": "https://archive.is/"
}

archive_collection_patterns = [
    "http://wayback.archive-it.org/([0-9]*)/[0-9]{14}/.*",
]

archive_collection_uri_patterns = [
    "(http://wayback.archive-it.org/[0-9]*)/[0-9]{14}/.*",
]

archive_collection_uri_prefixes = {
    "Archive-It": "https://archive-it.org/collections/{}"
}


def identify_archive(urim):
    """
    This function identifies the archive based on its URI-M.
    """

    ext = tldextract.extract(urim)

    domain = ext.registered_domain

    archive_name = "Unknown"

    if domain in archive_names:

        archive_name = archive_names[domain]

    return archive_name

def identify_collection(urim):
    """
    This function returns the collection identifier given a URI-M.

    If no collection identifer exists or can be determined, it returns None.
    """

    collection_id = None

    for pattern in archive_collection_patterns:
        m = re.match(pattern, urim)

        if m:
            collection_id = m.group(1)

    return collection_id

def get_collection_uri(urim):
    """
    This function returns the collection URI given a URI-M.

    If no collection can be determined from the URI-M, it returns None.
    """

    collection_id = identify_collection(urim)

    archive_name = identify_archive(urim)

    try:
        collection_uri = archive_collection_uri_prefixes[archive_name].format(collection_id)
    except KeyError:
        collection_uri = None

    return collection_uri

def get_archive_favicon(urim):
    """
    This function generates an archive favicon URI for a given URI-M.
    """

    archive_uri = get_archive_uri(urim)

    favicon_uri = "{}/favicon.ico".format(archive_uri)

    return favicon_uri

def get_archive_uri(urim):
    """
    This function queries the list of archives based on URI-M
    and returns the URI of the archive.
    """

    archive_name = identify_archive(urim)

    archive_uri = archive_uris[archive_name]

    return archive_uri    