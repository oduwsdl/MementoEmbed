import logging
import json
import traceback

from datetime import datetime

import requests_cache

from flask import render_template, request, make_response, Blueprint, current_app

from mementoembed.mementoresource import memento_resource_factory
from mementoembed.originalresource import OriginalResource
from mementoembed.textprocessing import extract_text_snippet, extract_title
from mementoembed.cachesession import CacheSession
from mementoembed.archiveresource import ArchiveResource
from mementoembed.imageselection import get_best_image
from mementoembed.version import __useragent__

from .errors import handle_errors

bp = Blueprint('services.memento', __name__)

module_logger = logging.getLogger('mementoembed.services.memento')

def contentdata(urim):

    output = {}

    httpcache = CacheSession(
        timeout=current_app.config['REQUEST_TIMEOUT_FLOAT'],
        user_agent=__useragent__,
        starting_uri=urim
        )

    memento = memento_resource_factory(urim, httpcache)

    output['urim'] = urim
    output['generation-time'] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    output['title'] = extract_title(memento.raw_content)
    output['snippet'] = extract_text_snippet(memento.raw_content)
    output['memento-datetime'] = memento.memento_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    response = make_response(json.dumps(output, indent=4))
    response.headers['Content-Type'] = 'application/json'
    return response, 200

def originaldata(urim):

    output = {}

    httpcache = CacheSession(
        timeout=current_app.config['REQUEST_TIMEOUT_FLOAT'],
        user_agent=__useragent__,
        starting_uri=urim
        )

    memento = memento_resource_factory(urim, httpcache)

    originalresource = OriginalResource(memento, httpcache)

    output['urim'] = urim
    output['generation-time'] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    output['original-uri'] = originalresource.uri
    output['original-domain'] = originalresource.domain
    output['original-favicon'] = originalresource.favicon
    output['original-linkstatus'] = originalresource.link_status

    response = make_response(json.dumps(output, indent=4))
    response.headers['Content-Type'] = 'application/json'
    return response, 200

def bestimage(urim):

    httpcache = CacheSession(
        timeout=current_app.config['REQUEST_TIMEOUT_FLOAT'],
        user_agent=__useragent__,
        starting_uri=urim
        )

    memento = memento_resource_factory(urim, httpcache)

    best_image_uri = get_best_image(memento.urim, httpcache)

    output = {}

    output['urim'] = urim
    output['best-image-uri'] = best_image_uri
    output['generation-time'] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    response = make_response(json.dumps(output, indent=4))
    response.headers['Content-Type'] = 'application/json'
    return response, 200

def archivedata(urim):

    httpcache = CacheSession(
        timeout=current_app.config['REQUEST_TIMEOUT_FLOAT'],
        user_agent=__useragent__,
        starting_uri=urim
        )

    archive = ArchiveResource(urim, httpcache)

    output = {}

    output['urim'] = urim
    output['generation-time'] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    output['archive-uri'] = archive.home_uri
    output['archive-name'] = archive.name
    output['archive-favicon'] = archive.favicon
    output['archive-collection-id'] = archive.collection_id
    output['archive-collection-name'] = archive.collection_name
    output['archive-collection-uri'] = archive.collection_uri

    response = make_response(json.dumps(output, indent=4))
    response.headers['Content-Type'] = 'application/json'
    return response, 200

@bp.route('/services/memento/contentdata/')
@bp.route('/services/memento/archivedata/')
@bp.route('/services/memento/originalresourcedata/')
@bp.route('/services/memento/bestimage/')
def no_urim():
    path = request.url_rule.rule
    return """WARNING: no URI-M submitted, please append a URI-M to {}
Example: {}/https://web.archive.org/web/20180515130056/http://www.cs.odu.edu/~mln/""".format(path, path), 200

@bp.route('/services/memento/contentdata/<path:subpath>')
def textinformation_endpoint(subpath):
    urim = subpath
    return handle_errors(contentdata, urim)

@bp.route('/services/memento/bestimage/<path:subpath>')
def bestimage_endpoint(subpath):
    urim = subpath
    return handle_errors(bestimage, urim)

@bp.route('/services/memento/archivedata/<path:subpath>')
def archivedata_endpoint(subpath):
    urim = subpath
    return handle_errors(archivedata, urim)

@bp.route('/services/memento/originalresourcedata/<path:subpath>')
def originaldata_endpoint(subpath):
    urim = subpath
    return handle_errors(originaldata, urim)
