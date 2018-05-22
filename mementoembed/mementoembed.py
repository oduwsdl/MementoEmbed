import os
import json
import base64
import binascii
import time
import aiu

import requests
import htmlmin

from datetime import datetime
from urllib.parse import urlparse, quote

from requests.structures import CaseInsensitiveDict
from flask import Flask, render_template, request, make_response
from filelock import Timeout, FileLock
from warcio import WARCWriter, ArchiveIterator, StatusAndHeaders

from .archiveinfo import get_archive_favicon, \
    identify_archive, identify_collection, \
    get_collection_uri, get_archive_uri

from .surrogate import Surrogate

app = Flask(__name__)

# user_agent_string = "MementoEmbed/0.0.1a0 See: https://github.com/shawnmjones/MementoEmbed"
user_agent_string = "ODU WS-DL Researcher Shawn M. Jones <sjone@cs.odu.edu>"

working_dir = "/app/mementoembed/working"

# pylint: disable=no-member
app.logger.info("loading Flask app for {}".format(app.name))

def get_record_dir(identifier):

    record_dir = "{}/{}".format(working_dir, identifier)

    if not os.path.exists(record_dir):
        try:
            os.makedirs(record_dir)
        except FileExistsError:
            # pylint: disable=no-member
            app.logger.warn("another process already created the record directory {}, ignoring...".format(record_dir))

    return record_dir

def fetch_web_resource(uri, identifier):
    """
    Acquires a URI-M and saves it to a WARC.
    """

    # pylint: disable=no-member
    app.logger.debug("fetching web resource for {}".format(uri))

    # record_dir = get_job_record(identifier)
    record_dir = get_record_dir(identifier)

        # pylint: disable=no-member

    warc_file_path = "{}/memento.warc.gz".format(record_dir)
    warc_lock_file_path = "{}/memento.warc.gz.lock".format(record_dir)

    if os.path.exists(warc_file_path):

        app.logger.debug("discovered both files, no need to download content from {}".format(uri))

    else:

        warc_file_lock = FileLock(warc_lock_file_path, timeout=1)
        warc_file_lock.acquire()

        app.logger.debug("no files from previous run, generating {}".format(warc_file_path))

        with open(warc_file_path, 'wb') as output:
            writer = WARCWriter(output, gzip=True)

            app.logger.debug("no files from previous run, downloading {}".format(uri))

            r = requests.get(uri, headers={'Accept-Encoding': 'identity'}, stream=True)

            headers_list = r.raw.headers.items()

            http_headers = StatusAndHeaders('200 OK', headers_list, protocol='HTTP/1.0')

            record = writer.create_warc_record(uri, 'response',
                                        payload=r.raw,
                                        http_headers=http_headers)

            writer.write_record(record)
    
        # pylint: disable=no-member
        app.logger.debug("attempting to release file lock")
        warc_file_lock.release()

    return record_dir

def fetch_web_resource_nonconcurrent(uri, identifier):

    app.logger.debug("fetching web resource for {}".format(uri))

    record_dir = get_record_dir(identifier)

    header_file_path = "{}/headers.json".format(record_dir)
    content_file_path = "{}/content.dat".format(record_dir)

    if os.path.exists(header_file_path) and os.path.exists(content_file_path):
        app.logger.info(
            "files for {} have already been downloaded to {}, not downloading again...".format(
                uri, identifier))
    else:
        app.logger.info(
            "files for {} not found, downloading...".format(uri)
        )
        r = requests.get(uri, headers={'Accept-Encoding': 'identity', 'User-Agent': user_agent_string}, stream=True)

        # TODO: raise an exception if not 200 so that we can throw a 501 later
        headers = r.headers

        app.logger.debug("headers returned: {}".format(headers))

        app.logger.debug("saving headers for {} to file {}".format(
            uri,  header_file_path
        ))

        with open(header_file_path, 'w') as h:
            json.dump(dict(headers), h)

        app.logger.debug("saving content for {} to file {}".format(
            uri,  content_file_path
        ))

        with open(content_file_path, 'w') as c:
            c.write(r.text)

    return record_dir
    

def get_content(uri, identifier):
    """
    Acquires the content of the entity of a memento.
    This is in a function to prevent race conditions when acquiring mementos.
    """

    record_dir = fetch_web_resource_nonconcurrent(uri, identifier)

    # with open("{}/memento.warc.gz".format(record_dir)) as stream:
    #     for record in ArchiveIterator(stream):
    #         if record.rec_type == 'response':
    #             content = record.raw_stream.read()

    content_file_path = "{}/content.dat".format(record_dir)

    with open(content_file_path) as c:
        content = c.read()

    app.logger.debug("returning content from {}".format(content_file_path))

    return content

def get_headers(uri, identifier):
    """
    Acquires the headers of a memento.
    This is in a function to prevent race conditions when acquiring mementos.
    """

    # pylint: disable=no-member
    app.logger.info("getting memento headers for {}".format(uri))

    headers = None

    record_dir = fetch_web_resource_nonconcurrent(uri, identifier)

    # with open("{}/memento.warc.gz".format(record_dir)) as stream:
    #     app.logger.debug("iterating through WARC records for file {}/memento.warc.gz".format(record_dir))
    #     for record in ArchiveIterator(stream):
    #         if record.rec_type == 'response':
    #             headers = record.http_headers
    #             # there really should only be 1 WARC record
    #             break

    header_file_path = "{}/headers.json".format(record_dir)
    
    with open(header_file_path) as h:
        headers = json.load(h)

    iheaders = CaseInsensitiveDict(data=headers)

    app.logger.debug("returning case-insensitive headers from {}".format(header_file_path))

    return iheaders

@app.route('/')
def front_page():
    return render_template('index.html')

@app.route('/services/oembed', methods=['GET', 'HEAD'])
def oembed_endpoint():
#     """
#     Ref: https://oembed.com

#     Request options:
#     url (required)
#         The URL to retrieve embedding information for.
#     maxwidth (optional)
#         The maximum width of the embedded resource. Only applies to some resource types (as specified below). 
#         For supported resource types, this parameter must be respected by providers.
#     maxheight (optional)
#         The maximum height of the embedded resource. Only applies to some resource types (as specified below). 
#         For supported resource types, this parameter must be respected by providers.
#     format (optional)
#         The required response format. When not specified, the provider can return any valid response format. 
#         When specified, the provider must return data in the request format, else return an error (see below for error codes).

#     JSON responses must contain well formed JSON and must use the mime-type of application/json. The JSON response 
#     format may be requested by the consumer by specifying a format of json.

#     Response fields:
#     type (required)
#         The resource type. Valid values, along with value-specific parameters, are described below.
#     version (required)
#         The oEmbed version number. This must be 1.0.
#     title (optional)
#         A text title, describing the resource.
#     author_name (optional)
#         The name of the author/owner of the resource.
#     author_url (optional)
#         A URL for the author/owner of the resource.
#     provider_name (optional)
#         The name of the resource provider.
#     provider_url (optional)
#         The url of the resource provider.
#     cache_age (optional)
#         The suggested cache lifetime for this resource, in seconds. Consumers may choose to use this value or not.
#     thumbnail_url (optional)
#         A URL to a thumbnail image representing the resource. The thumbnail must respect any maxwidth and maxheight parameters. 
#         If this parameter is present, thumbnail_width and thumbnail_height must also be present.
#     thumbnail_width (optional)
#         The width of the optional thumbnail. If this parameter is present, thumbnail_url and thumbnail_height must also be present.
#     thumbnail_height (optional)
#         The height of the optional thumbnail. If this parameter is present, thumbnail_url and thumbnail_width must also be present.

#     For rich data fields:

#     html (required)
#         The HTML required to display the resource. The HTML should have no padding or margins. 
#         Consumers may wish to load the HTML in an off-domain iframe to avoid XSS vulnerabilities. 
#         The markup should be valid XHTML 1.0 Basic.
#     width (required)
#         The width in pixels required to display the HTML.
#     height (required)
#         The height in pixels required to display the HTML.

#     Error codes:

#     404 Not Found
#         The provider has no response for the requested url parameter. This allows providers to be broad in their URL scheme,
#         and then determine at call time if they have a representation to return.
#     501 Not Implemented
#         The provider cannot return a response in the requested format. This should be sent when (for example) the request
#         includes format=xml and the provider doesn't support XML responses. However, providers are encouraged to support both JSON and XML.
#     401 Unauthorized
#         The specified URL contains a private (non-public) resource. The consumer should provide a link directly to the resource
#         instead of embedding any extra information, and rely on the provider to provide access control.

#     Example oEmbed response for Flickr:
#     {
#         "version": "1.0",
#         "type": "photo",
#         "width": 240,
#         "height": 160,
#         "title": "ZB8T0193",
#         "url": "http://farm4.static.flickr.com/3123/2341623661_7c99f48bbf_m.jpg",
#         "author_name": "Bees",
#         "author_url": "http://www.flickr.com/photos/bees/",
#         "provider_name": "Flickr",
#         "provider_url": "http://www.flickr.com/"
#     }
#     """

    urim = None
    urir = None
    striking_image = None
    archive_uri = None
    archive_favicon_uri = None
    collection_id = None
    collection_uri = None
    archive_collection_name = None
    archive_name = None
    original_favicon_uri = None
    original_domain = None
    original_link_status = None
    surrogate_creation_time = None
    memento_datetime = None
    title = None
    text_snippet = None

    url = request.args.get("url")
    responseformat = request.args.get("format")

    # JSON is the default
    if responseformat == None:
        responseformat = "json"

    if responseformat != "json":
        return "The provider cannot return a response in the requested format.", 501

    app.logger.debug("received url {}".format(url))
    app.logger.debug("format: {}".format(responseformat))

    # TODO: implement archivenow functionality
    urim = url
    identifier = quote(urim, safe="")

    try:
        archive_name = identify_archive(urim)
        archive_uri = get_archive_uri(urim)
        archive_favicon_uri = get_archive_favicon(urim)
    except KeyError:
        return "URI-M {} belongs to an archive or site that is not supported by MementoEmbed".format(urim), 404

    collection_uri = get_collection_uri(urim)

    app.logger.debug("collection URI is {}".format(collection_uri))

    if collection_uri:
        collection_id = identify_collection(urim)

        record_dir = get_record_dir(identifier)

        try:
            aic = aiu.ArchiveItCollection(
                collection_id=collection_id,
                logger=app.logger,
                working_directory=record_dir
                )

            archive_collection_name = aic.get_collection_name()

        except aiu.ArchiveItCollectionException:
            return "Cannot determine information about archive collection", 500

    output = {}

    output["type"] = "rich"
    output["version"] = "1.0"

    output["url"] = urim
    output["provider_name"] = archive_name
    output["provider_uri"] = archive_uri

    surrogate_creation_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    app.logger.debug("oembed: acquiring memento headers and content for URI-M: {}".format(urim))

    try:
        headers = get_headers(urim, identifier)
        app.logger.debug("acquired memento headers")

        content = get_content(urim, identifier)
        app.logger.debug("acquired memento content")
    except requests.exceptions.ConnectTimeout:
        return "Connection timed out trying to load URI-M {}".format(urim), 504
    except requests.exceptions.ConnectionError:
        return "Requesting the URI-M {} produced a connection error".format(urim), 503

    # TODO: this is a convention, but not how one discovers a favicon
    # original_favicon_uri = "https://{}/favicon.ico".format(original_domain)

    s = Surrogate(
        uri=urim,
        content=content,
        response_headers=headers,
        logger=app.logger
    )

    original_domain = s.original_domain
    urir = s.original_uri
    original_link_status = s.original_link_status

    app.logger.debug("extracting title for {}".format(urim))
    title = s.title

    app.logger.debug("extracting text snippet for {}".format(urim))
    text_snippet = s.text_snippet

    app.logger.debug("extracting image for {}".format(urim))
    striking_image = s.striking_image

    app.logger.debug("extracting memento-datetime from {}".format(urim))
    memento_datetime = s.memento_datetime.strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    original_favicon_uri = s.original_favicon

    urlroot = request.url_root
    urlroot = urlroot if urlroot[-1] != '/' else urlroot[0:-1]

    app.logger.info("generating oEmbed output for {}".format(urim))
    output["html"] = htmlmin.minify( render_template(
        "social_card.html",
        urim = urim,
        urir = urir,
        image = striking_image,
        archive_uri = archive_uri,
        archive_favicon = archive_favicon_uri,
        archive_collection_id = collection_id,
        archive_collection_uri = collection_uri,
        archive_collection_name = archive_collection_name,
        archive_name = archive_name,
        original_favicon = original_favicon_uri,
        original_domain = original_domain,
        original_link_status = original_link_status,
        surrogate_creation_time = surrogate_creation_time,
        memento_datetime = memento_datetime,
        me_title = title,
        me_snippet = text_snippet,
        server_domain = urlroot
    ), remove_empty_space=True, 
    remove_optional_attribute_quotes=False )

    output["width"] = 500

    #TODO: fix this to the correct height!
    output["height"] = 200

    response = make_response(json.dumps(output, indent=4))
    response.headers['Content-Type'] = 'application/json'

    app.logger.info("returning output as application/json...")

    return response

if __name__ == '__main__':
    app.run()