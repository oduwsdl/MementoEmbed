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