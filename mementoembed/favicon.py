import tldextract

from datetime import datetime

from bs4 import BeautifulSoup

def favicon_resource_test(response):

    good = False

    if response.status_code == 200:

        try:

            if 'image/' in response.headers['content-type']:
                good = True

        # this should not happen, but some server may not return a content-type
        except KeyError:
            good = False

    return good

def get_favicon_from_html(content):
    # search HTML for meta tags containing the relation "icon" or "shortcut"
    
    favicon_uri = None

    soup = BeautifulSoup(content, 'html5lib')

    links = soup.find_all("link")

    for link in links:

        if 'icon' in link['rel']:
            favicon_uri = link['href']
            break

    # if that fails, try the older, nonstandard relation 'shortcut'
    if favicon_uri == None:

        for link in links:

            if 'shortcut' in link['rel']:
                favicon_uri = link['href']
                break

    return favicon_uri

def get_favicon_from_google_service(http_cache, uri):
    """
        Get the favicon from the Google service.

        This is a last-ditch effort to get a favicon.

        The Google service returns a default if it has no URI in the cache.
    """

    favicon_uri = None

    domain = tldextract.extract(uri).registered_domain

    google_favicon_uri = "https://www.google.com/s2/favicons?domain={}".format(domain)

    r = http_cache.get(google_favicon_uri)

    if favicon_resource_test(r) is True:

        favicon_uri = google_favicon_uri

    return favicon_uri

def construct_conventional_favicon_uri(scheme, domain):

    favicon_uri = "{}://{}/favicon.ico".format(scheme, domain)

    return favicon_uri

def find_conventional_favicon_on_live_web(scheme, domain, http_cache):

    favicon_uri = None

    candidate_favicon_uri = construct_conventional_favicon_uri(scheme, domain)

    r = http_cache.get(candidate_favicon_uri)

    if favicon_resource_test(r) is True:

        favicon_uri = candidate_favicon_uri

    return favicon_uri

def query_timegate_for_favicon(timegate_stem, candidate_favicon_uri, accept_datetime, http_cache):

    favicon_uri = None
    favicon_timegate = None

    accept_datetime_str = accept_datetime.strftime("%a, %d %b %Y %H:%M:%S GMT")

    if timegate_stem[-1] != '/':
        favicon_timegate = '/'.join([timegate_stem, candidate_favicon_uri])
    else:
        favicon_timegate = timegate_stem + candidate_favicon_uri

    r = http_cache.get(favicon_timegate, headers={'accept-datetime': accept_datetime_str})

    if r.status_code == 302:

        candidate_favicon_uri = r.headers['location']

        r = http_cache.get(candidate_favicon_uri)

        if favicon_resource_test(r) is True:

            favicon_uri = candidate_favicon_uri

    return favicon_uri

def get_favicon_from_resource_content(uri, http_cache):

    favicon_uri = None

    r = http_cache.get(uri)

    candidate_favicon_uri = get_favicon_from_html(r.text)

    if candidate_favicon_uri is not None:

        r = http_cache.get(candidate_favicon_uri)

        if favicon_resource_test(r) is True:

            favicon_uri = candidate_favicon_uri

    return favicon_uri