from flask import Flask, render_template

app = Flask(__name__)

@app.route('/', methods=['GET', 'HEAD'])
def front_page():
    # return render_template('front_page.html')
    return "Hello World!"

@app.route('/socialcard/<path:uri>', methods=['GET', 'HEAD'])
def make_social_card(uri=None):
    # return render_template('social_card.html', urim=uri)
    return "Hello {}}!".format(uri)

@app.route('/services/oembed/')
def oembed_endpoint(format="json", url=None):
"""
    Ref: https://oembed.com

    Request options:
    url (required)
        The URL to retrieve embedding information for.
    maxwidth (optional)
        The maximum width of the embedded resource. Only applies to some resource types (as specified below). 
        For supported resource types, this parameter must be respected by providers.
    maxheight (optional)
        The maximum height of the embedded resource. Only applies to some resource types (as specified below). 
        For supported resource types, this parameter must be respected by providers.
    format (optional)
        The required response format. When not specified, the provider can return any valid response format. 
        When specified, the provider must return data in the request format, else return an error (see below for error codes).

    JSON responses must contain well formed JSON and must use the mime-type of application/json. The JSON response 
    format may be requested by the consumer by specifying a format of json.

    Response fields:
    type (required)
        The resource type. Valid values, along with value-specific parameters, are described below.
    version (required)
        The oEmbed version number. This must be 1.0.
    title (optional)
        A text title, describing the resource.
    author_name (optional)
        The name of the author/owner of the resource.
    author_url (optional)
        A URL for the author/owner of the resource.
    provider_name (optional)
        The name of the resource provider.
    provider_url (optional)
        The url of the resource provider.
    cache_age (optional)
        The suggested cache lifetime for this resource, in seconds. Consumers may choose to use this value or not.
    thumbnail_url (optional)
        A URL to a thumbnail image representing the resource. The thumbnail must respect any maxwidth and maxheight parameters. 
        If this parameter is present, thumbnail_width and thumbnail_height must also be present.
    thumbnail_width (optional)
        The width of the optional thumbnail. If this parameter is present, thumbnail_url and thumbnail_height must also be present.
    thumbnail_height (optional)
        The height of the optional thumbnail. If this parameter is present, thumbnail_url and thumbnail_width must also be present.

    For rich data fields:

    html (required)
        The HTML required to display the resource. The HTML should have no padding or margins. 
        Consumers may wish to load the HTML in an off-domain iframe to avoid XSS vulnerabilities. 
        The markup should be valid XHTML 1.0 Basic.
    width (required)
        The width in pixels required to display the HTML.
    height (required)
        The height in pixels required to display the HTML.

    Error codes:

    404 Not Found
        The provider has no response for the requested url parameter. This allows providers to be broad in their URL scheme,
        and then determine at call time if they have a representation to return.
    501 Not Implemented
        The provider cannot return a response in the requested format. This should be sent when (for example) the request
        includes format=xml and the provider doesn't support XML responses. However, providers are encouraged to support both JSON and XML.
    401 Unauthorized
        The specified URL contains a private (non-public) resource. The consumer should provide a link directly to the resource
        instead of embedding any extra information, and rely on the provider to provide access control.

    Example oEmbed response for Flickr:
    {
        "version": "1.0",
        "type": "photo",
        "width": 240,
        "height": 160,
        "title": "ZB8T0193",
        "url": "http://farm4.static.flickr.com/3123/2341623661_7c99f48bbf_m.jpg",
        "author_name": "Bees",
        "author_url": "http://www.flickr.com/photos/bees/",
        "provider_name": "Flickr",
        "provider_url": "http://www.flickr.com/"
    }
"""
    return "oEmbed endpoint not yet implemented"

if __name__ == '__main__':
    app.run()