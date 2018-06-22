import tldextract

from bs4 import BeautifulSoup

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

def get_favicon_from_google_service(session, uri):
    """
        Get the favicon from the Google service.

        This is a last-ditch effort to get a favicon.

        The Google service returns a default if it has no URI in the cache.
    """

    favicon_uri = None

    domain = tldextract.extract(uri).registered_domain

    google_favicon_uri = "https://www.google.com/s2/favicons?domain={}".format(domain)

    r = session.get(google_favicon_uri)

    if r.status_code == 200:
        favicon_uri = google_favicon_uri

    return favicon_uri