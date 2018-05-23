import os
import json
import base64
import binascii
import time
import aiu

import requests
import htmlmin
import dicttoxml

from datetime import datetime
from urllib.parse import urlparse, quote

from requests.structures import CaseInsensitiveDict

from cachecontrol import CacheControl
from cachecontrol.caches.file_cache import FileCache

from flask import Flask, render_template, request, make_response, redirect
from filelock import Timeout, FileLock
from warcio import WARCWriter, ArchiveIterator, StatusAndHeaders

from .archiveinfo import get_archive_favicon, \
    identify_archive, identify_collection, \
    get_collection_uri, get_archive_uri

from .mementosurrogate import MementoSurrogate, NotMementoException

app = Flask(__name__)

# user_agent_string = "MementoEmbed/0.0.1a0 See: https://github.com/shawnmjones/MementoEmbed"
user_agent_string = "ODU WS-DL Researcher Shawn M. Jones <sjone@cs.odu.edu>"

working_dir = "/app/mementoembed/working"

# pylint: disable=no-member
app.logger.info("loading Flask app for {}".format(app.name))

@app.route('/', methods=['GET', 'HEAD'])
def front_page():
#     return redirect("/?", code=302)

# @app.route('/?', methods=['GET', 'HEAD'])
# def real_front_page():
    return render_template('index.html')

@app.route('/services/oembed', methods=['GET', 'HEAD'])
def oembed_endpoint():

    urim = request.args.get("url")
    responseformat = request.args.get("format")

    # JSON is the default
    if responseformat == None:
        responseformat = "json"

    if responseformat != "json":
        if responseformat != "xml":
            return "The provider cannot return a response in the requested format.", 501

    app.logger.debug("received url {}".format(urim))
    app.logger.debug("format: {}".format(responseformat))

    if os.environ.get('FLASK_ENV'):
        if 'development' in os.environ.get('FLASK_ENV').lower():
            session = CacheControl(requests.session(), cache=FileCache('.web_cache', forever=True))
        else:
            session = CacheControl(requests.session(), cache=FileCache('.web_cache'))    
    else:
        session = CacheControl(requests.session(), cache=FileCache('.web_cache'))

    try:
        
        s = MementoSurrogate(
            urim=urim,
            session=session,
            logger=app.logger
        )

        output = {}

        output["type"] = "rich"
        output["version"] = "1.0"

        output["url"] = urim
        output["provider_name"] = s.archive_name
        output["provider_uri"] = s.archive_uri

        urlroot = request.url_root
        urlroot = urlroot if urlroot[-1] != '/' else urlroot[0:-1]

        app.logger.info("generating oEmbed output for {}".format(urim))
        output["html"] = htmlmin.minify( render_template(
            "social_card.html",
            urim = urim,
            urir = s.original_uri,
            image = s.striking_image,
            archive_uri = s.archive_uri,
            archive_favicon = s.archive_favicon,
            archive_collection_id = s.collection_id,
            archive_collection_uri = s.collection_uri,
            archive_collection_name = s.collection_name,
            archive_name = s.archive_name,
            original_favicon = s.original_favicon,
            original_domain = s.original_domain,
            original_link_status = s.original_link_status,
            surrogate_creation_time = s.creation_time,
            memento_datetime = s.memento_datetime,
            me_title = s.title,
            me_snippet = s.text_snippet,
            server_domain = urlroot
        ), remove_empty_space=True, 
        remove_optional_attribute_quotes=False )

        output["width"] = 500

        #TODO: fix this to the correct height!
        output["height"] = 200

        if responseformat == "json":
            response = make_response(json.dumps(output, indent=4))
            response.headers['Content-Type'] = 'application/json'
        else:
            response = make_response( dicttoxml.dicttoxml(output, custom_root='oembed') )
            response.headers['Content-Type'] = 'text/xml'

        app.logger.info("returning output as application/json...")

    except NotMementoException:
        return render_template(
            'make_your_own_memento.html',
            urim = urim
            ), 400

    return response

if __name__ == '__main__':
    app.run()