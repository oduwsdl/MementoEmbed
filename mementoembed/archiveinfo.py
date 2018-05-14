import re
import tldextract

archive_names = {
    "archive-it.org": "Archive-It",
    "archive.org": "Internet Archive",
    "webcitation.org": "Web Cite",
    "archive.is": "Archive.is"
}

archive_collections = [
    "http://wayback.archive-it.org/([0-9]*)/[0-9]{14}/.*",
]

archive_mappings = {
    "wayback.archive-it.org": ( '/http', 'id_/http' ),
    "web.archive.org": ( '/http', 'id_/http' )
}

def generate_raw_urim(urim):
    """Generates a raw URI-M based on the archive it belongs to. Supported
    URI patterns are found in `archive_mappings`.
    """

    raw_urim = urim

    for domainname in archive_mappings:

        if domainname in urim:

            search_pattern = archive_mappings[domainname][0]
            replacement_pattern = archive_mappings[domainname][1]

            # TODO: some urims have no /http pattern, e.g. https://web.archive.org/web/20171205043718/odu.edu/compsci

            # if urim is already a raw urim, do nothing
            if replacement_pattern not in urim:

                raw_urim = urim.replace(
                    search_pattern, replacement_pattern
                )

            break

    return raw_urim

def identify_archive(urim):

    ext = tldextract.extract(urim)

    domain = ext.registered_domain

    archive_name = "Unknown"

    if domain in archive_names:

        archive_name = archive_names[domain]

    return archive_name

def identify_collection(urim):

    for pattern in archive_collections:
        m = re.match(pattern, urim)

        if m:
            colleciton_id = m.group(1)

    return colleciton_id

def get_archive_favicon(urim):

    ext = tldextract.extract(urim)

    domain = ext.registered_domain

    favicon_uri = "https://{}/favicon.ico".format(domain)

    return favicon_uri