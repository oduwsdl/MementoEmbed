import os
import logging
import json
import traceback
import hashlib

import htmlmin
import requests_cache

from flask import render_template, request, Blueprint, current_app, make_response

from mementoembed.mementosurrogate import MementoSurrogate
from mementoembed.mementothumbnail import MementoThumbnail, \
    MementoThumbnailGenerationError, MementoThumbnailFolderNotFound
from mementoembed.cachesession import CacheSession
from mementoembed.version import __useragent__

from .errors import handle_errors

module_logger = logging.getLogger('mementoembed.services.product')

bp = Blueprint('services.product', __name__)

def generate_social_card_html(urim, surrogate, urlroot):

    return htmlmin.minify( render_template(
        "new_social_card.html",
        urim = urim,
        urir = surrogate.original_uri,
        image = surrogate.striking_image,
        archive_uri = surrogate.archive_uri,
        archive_favicon = surrogate.archive_favicon,
        archive_collection_id = surrogate.collection_id,
        archive_collection_uri = surrogate.collection_uri,
        archive_collection_name = surrogate.collection_name,
        archive_name = surrogate.archive_name,
        original_favicon = surrogate.original_favicon,
        original_domain = surrogate.original_domain,
        original_link_status = surrogate.original_link_status,
        surrogate_creation_time = surrogate.creation_time,
        memento_datetime = surrogate.memento_datetime,
        me_title = surrogate.title,
        me_snippet = surrogate.text_snippet
    ) + '<script async src="{}/static/js/mementoembed.js" charset="utf-8"></script>'.format(urlroot), 
    remove_empty_space=True, 
    remove_optional_attribute_quotes=False )

def generate_socialcard_response(urim):

    httpcache = CacheSession(
        timeout=current_app.config['REQUEST_TIMEOUT_FLOAT'],
        user_agent=__useragent__,
        starting_uri=urim
        )

    s = MementoSurrogate(
        urim,
        httpcache
    )

    urlroot = request.url_root
    urlroot = urlroot if urlroot[-1] != '/' else urlroot[0:-1]
    
    return generate_social_card_html(urim, s, urlroot), 200

@bp.route('/services/product/socialcard/<path:subpath>')
def socialcard_endpoint(subpath):

    urim = subpath
    return handle_errors(generate_socialcard_response, urim)

@bp.route('/services/product/thumbnail/<path:subpath>')
def thumbnail_endpoint(subpath):

    try:

        # TODO: test that subpath is actually a memento
        module_logger.info("ummm...")

        if current_app.config['ENABLE_THUMBNAILS'] == "Yes":
            urim = subpath

            module_logger.info("Beginning thumbnail generation")

            mt = MementoThumbnail(
                __useragent__,
                current_app.config['THUMBNAIL_WORKING_FOLDER'],
                current_app.config['THUMBNAIL_SCRIPT_PATH']
            )

            try:

                mt.viewport_height = int(current_app.config['THUMBNAIL_VIEWPORT_HEIGHT'])
                mt.viewport_width = int(current_app.config['THUMBNAIL_VIEWPORT_WIDTH'])
                mt.timeout = int(current_app.config['THUMBNAIL_TIMEOUT'])

                data = mt.generate_thumbnail(urim)

                response = make_response(data)
                response.headers['Content-Type'] = 'image/png'
                response.headers['Preference-Applied'] = \
                    "viewport_width={},viewport_height={}" \
                    "thumbnail_width={},thumbnail_height={}".format(
                        mt.viewport_width, mt.viewport_height,
                        mt.width, mt.height)

                module_logger.info("Finished with thumbnail generation")

                return response, 200

            except MementoThumbnailFolderNotFound:

                msg = "Thumbnail folder {} does not exist".format(current_app.config['THUMBNAIL_WORKING_FOLDER'])
                module_logger.exception(msg)
                    
                output = {
                    "error": msg,
                    "error details": repr(traceback.format_exc())
                }

                response = make_response(json.dumps(output))
                response.headers['Content-Type'] = 'application/json'

                return response, 500

            except MementoThumbnailGenerationError:

                output = {
                    "error": "a thumbnail failed to generated in {} seconds".format(mt.timeout),
                    "error details": repr(traceback.format_exc())
                }

                response = make_response(json.dumps(output))
                response.headers['Content-Type'] = 'application/json'

                return response, 500
            
        else:
            return "The thumbnail service has been disabled by the system administrator", 200

    except KeyError:
            return "The thumbnail service is disabled by default", 200
