import logging

import tldextract

from datetime import datetime

from bs4 import BeautifulSoup
from requests.exceptions import RequestException

module_logger = logging.getLogger('mementoembed.favicon')

def favicon_resource_test(response):

    module_logger.debug("testing favicon at {}".format(response.url))

    good = False

    if response.status_code == 200:

        try:

            if 'image/' in response.headers['content-type']:

                if len(response.content) > 0:
                    good = True

        # this should not happen, but some server may not return a content-type
        except KeyError:
            module_logger.warning("headers for {} did not contain a "
                "content-type, marking favicon as unsuitable".format(
                    response.url))
            good = False

    return good

def get_favicon_from_html(content):
    # search HTML for meta tags containing the relation "icon" or "shortcut"
    
    favicon_uri = None

    try:
        soup = BeautifulSoup(content, 'html5lib')
    except Exception:
        module_logger.exception("failed to open document using BeautifulSoup")
        return favicon_uri

    try:
        links = soup.find_all("link")
    except Exception:
        module_logger.exception("failed to find link tags in document using BeautifulSoup")
        return favicon_uri

    for link in links:

        module_logger.debug("looking at link element {}".format(link))

        try:
            if 'icon' in link['rel']:
                favicon_uri = link['href']
                module_logger.debug("found favicon with 'icon' relation at {}".format(favicon_uri))
                break
        except KeyError:
            module_logger.exception("there was no 'rel' attribute in this link tag: {}".format(link))
            favicon_uri == None

    # if that fails, try the older, nonstandard relation 'shortcut'
    if favicon_uri == None:

        module_logger.debug("failed to find favicon with 'icon', trying 'shortcut'")

        for link in links:

            try:
                if 'shortcut' in link['rel']:
                    favicon_uri = link['href']
                    module_logger.debug("found favicon with 'shortcut' relation at {}".format(favicon_uri))
                    break
            except KeyError:
                module_logger.exception("there was no 'rel' attribute in this link tag: {}".format(link))
                favicon_uri == None

    # if that fails, maybe they used both 'shortcut' and 'icon' together
    # see: https://wayback.archive-it.org/2358/20110211072257/http://news.blogs.cnn.com/category/world/egypt-world-latest-news/
    if favicon_uri == None:

        module_logger.debug("failed to find favicon with 'icon' or 'shortcut', trying 'shortcut icon'")

        for link in links:

            try:
                if 'shortcut icon' in link['rel']:
                    favicon_uri = link['href']
                    module_logger.debug("found favicon with 'shortcut icon' relation at {}".format(favicon_uri))
                    break
            except KeyError:
                module_logger.exception("there was no 'rel' attribute in this link tag: {}".format(link))
                favicon_uri == None

    module_logger.debug("returning favicon: {}".format(favicon_uri))

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

    try:

        r = http_cache.get(google_favicon_uri)

        if favicon_resource_test(r) is True:

            favicon_uri = google_favicon_uri

    except RequestException:
        module_logger.exception("Failed to download favicon {} from Google Favicon service, skipping...".format(google_favicon_uri))

    return favicon_uri

def construct_conventional_favicon_uri(scheme, domain):

    favicon_uri = "{}://{}/favicon.ico".format(scheme, domain)

    return favicon_uri

def find_conventional_favicon_on_live_web(scheme, domain, http_cache):

    favicon_uri = None

    candidate_favicon_uri = construct_conventional_favicon_uri(scheme, domain)

    try:

        r = http_cache.get(candidate_favicon_uri)

        if favicon_resource_test(r) is True:

            favicon_uri = candidate_favicon_uri

    except RequestException:
        module_logger.exception("Failed to download favicon {} from live web, skipping...".format(candidate_favicon_uri))

    return favicon_uri

def query_timegate_for_favicon(timegate_stem, candidate_favicon_uri, accept_datetime, http_cache):

    favicon_uri = None
    favicon_timegate = None

    accept_datetime_str = accept_datetime.strftime("%a, %d %b %Y %H:%M:%S GMT")

    if timegate_stem[-1] != '/':
        favicon_timegate = '/'.join([timegate_stem, candidate_favicon_uri])
    else:
        favicon_timegate = timegate_stem + candidate_favicon_uri

    try:

        r = http_cache.get(favicon_timegate, headers={'accept-datetime': accept_datetime_str})

        if r.status_code == 200:

            # candidate_favicon_uri = r.headers['location']
            candidate_favicon_uri = r.url

            try:
                r = http_cache.get(candidate_favicon_uri)

                if favicon_resource_test(r) is True:

                    favicon_uri = candidate_favicon_uri

            except RequestException:
                module_logger.exception("Failed to download favicon {}, skipping...".format(candidate_favicon_uri))


    except RequestException:
        module_logger.exception("Failed to access timegate {}, skipping...".format(favicon_timegate))

    return favicon_uri

def get_favicon_from_resource_content(uri, http_cache):

    module_logger.debug("searching for favicon in content of URI {}".format(uri))

    favicon_uri = None

    try:
        r = http_cache.get(uri)
        candidate_favicon_uri = get_favicon_from_html(r.text)

    except RequestException as e:
        module_logger.warn("Failed to download favicon discovered in HTML of URI {}, skipping...".format(uri))
        module_logger.debug("Favicon from HTML failure for URI {}, details: {}".format(uri, e))
        candidate_favicon_uri = None

    if candidate_favicon_uri is not None:

        try:
            r = http_cache.get(candidate_favicon_uri)

            if favicon_resource_test(r) is True:

                favicon_uri = candidate_favicon_uri

        except RequestException as e:
            module_logger.warn("Failed to download favicon {} discovered in HTML of URI {}, skipping...".format(candidate_favicon_uri, uri))
            module_logger.debug("Favicon from HTML failure for URI {}, details: {}".format(uri, e))


    return favicon_uri
