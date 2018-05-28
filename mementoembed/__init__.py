import os
import json

import htmlmin
import dicttoxml
import requests

from flask import Flask, request, render_template, make_response
from cachecontrol import CacheControl
from cachecontrol.caches.file_cache import FileCache

from .mementosurrogate import MementoSurrogate, NotMementoException, \
    MementoConnectionTimeout, MementoImageConnectionError, \
    MementoImageConnectionTimeout

__all__ = [
    "MementoSurrogate", "NotMementoException", "MementoConnectionTimeout",
    "MementoImageConnectionError", "MementoImageConnectionTimeout"
    ]

user_agent_string = "ODU WS-DL Researcher Shawn M. Jones <sjone@cs.odu.edu>"

def create_app():

    app = Flask(__name__, instance_relative_config=True)

    # pylint: disable=no-member
    app.logger.info("loading Flask app for {}".format(app.name))

    #pylint: disable=unused-variable
    @app.route('/', methods=['GET', 'HEAD'])
    def front_page():
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

    return app
