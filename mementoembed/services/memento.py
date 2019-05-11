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
from mementoembed.seedresource import SeedResource
from mementoembed.imageselection import get_best_image, convert_imageuri_to_pngdata_uri, generate_images_and_scores
from mementoembed.version import __useragent__

from .errors import handle_errors
from . import extract_urim_from_request_path

bp = Blueprint('services.memento', __name__)

module_logger = logging.getLogger('mementoembed.services.memento')

def contentdata(urim, preferences):

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

def originaldata(urim, preferences):

    output = {}

    httpcache = CacheSession(
        timeout=current_app.config['REQUEST_TIMEOUT_FLOAT'],
        user_agent=__useragent__,
        starting_uri=urim
        )

    memento = memento_resource_factory(urim, httpcache)

    originalresource = OriginalResource(memento, httpcache)

    if preferences['datauri_favicon'].lower() == 'yes':

        try:
            original_favicon = convert_imageuri_to_pngdata_uri(
                originalresource.favicon, httpcache, 16, 16
            )
        except ValueError as e:

            module_logger.exception(
                "an error occurred while generating a data URI for an original resource favicon"
                )

            if str(e) == "not enough image data":
                original_favicon=""

            else:
                raise e

    else:
        original_favicon = originalresource.favicon

    output['urim'] = urim
    output['generation-time'] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    output['original-uri'] = originalresource.uri
    output['original-domain'] = originalresource.domain
    output['original-favicon'] = original_favicon
    output['original-linkstatus'] = originalresource.link_status

    response = make_response(json.dumps(output, indent=4))
    response.headers['Content-Type'] = 'application/json'

    response.headers['Preference-Applied'] = \
        "datauri_favicon={}".format(preferences['datauri_favicon'])

    return response, 200

def bestimage(urim, preferences):

    httpcache = CacheSession(
        timeout=current_app.config['REQUEST_TIMEOUT_FLOAT'],
        user_agent=__useragent__,
        starting_uri=urim
        )

    memento = memento_resource_factory(urim, httpcache)

    best_image_uri = get_best_image(
        memento.im_urim, 
        httpcache,
        current_app.config['DEFAULT_IMAGE_URI']
    )

    if preferences['datauri_image'].lower() == 'yes':
        if best_image_uri[0:5] != 'data:':
            best_image_uri = convert_imageuri_to_pngdata_uri(
                best_image_uri, httpcache, 96
            )

    output = {}

    output['urim'] = urim
    output['best-image-uri'] = best_image_uri
    output['generation-time'] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    response = make_response(json.dumps(output, indent=4))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Preference-Applied'] = \
        "datauri_image={}".format(preferences['datauri_image'])

    return response, 200

def imagedata(urim, preferences):

    httpcache = CacheSession(
        timeout=current_app.config['REQUEST_TIMEOUT_FLOAT'],
        user_agent=__useragent__,
        starting_uri=urim
        )

    memento = memento_resource_factory(urim, httpcache)

    output = {}

    output['urim'] = urim
    output['processed urim'] = memento.im_urim
    output['generation-time'] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    output['images'] = generate_images_and_scores(urim, httpcache)

    response = make_response(json.dumps(output, indent=4))
    response.headers['Content-Type'] = 'application/json'

    return response, 200

def archivedata(urim, preferences):

    httpcache = CacheSession(
        timeout=current_app.config['REQUEST_TIMEOUT_FLOAT'],
        user_agent=__useragent__,
        starting_uri=urim
        )

    # TODO: only here because we need to detect NotAMemento, need a better solution
    memento = memento_resource_factory(urim, httpcache) 

    archive = ArchiveResource(urim, httpcache)

    if preferences['datauri_favicon'].lower() == 'yes':
        archive_favicon = convert_imageuri_to_pngdata_uri(
            archive.favicon, httpcache, 16, 16
        )
    else:
        archive_favicon = archive.favicon

    output = {}

    output['urim'] = urim
    output['generation-time'] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    output['archive-uri'] = archive.home_uri
    output['archive-name'] = archive.name
    output['archive-favicon'] = archive_favicon
    output['archive-collection-id'] = archive.collection_id
    output['archive-collection-name'] = archive.collection_name
    output['archive-collection-uri'] = archive.collection_uri

    response = make_response(json.dumps(output, indent=4))
    response.headers['Content-Type'] = 'application/json'

    response.headers['Preference-Applied'] = \
        "datauri_favicon={}".format(preferences['datauri_favicon'])

    return response, 200

def seeddata(urim, preferences):

    httpcache = CacheSession(
        timeout=current_app.config['REQUEST_TIMEOUT_FLOAT'],
        user_agent=__useragent__,
        starting_uri=urim
        )

    memento = memento_resource_factory(urim, httpcache)

    sr = SeedResource(memento, httpcache)

    output = {}

    output['urim'] = urim
    output['generation-time'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    output['timemap'] = sr.urit
    output['original-url'] = sr.urir
    output['memento-count'] = sr.mementocount()
    output['first-memento-datetime'] = sr.first_mdt().strftime("%Y-%m-%dT%H:%M:%SZ")
    output['first-urim'] = sr.first_urim()
    output['last-memento-datetime'] = sr.last_mdt().strftime("%Y-%m-%dT%H:%M:%SZ")
    output['last-urim'] = sr.last_urim()
    output['metadata'] = sr.seed_metadata()

    response = make_response(json.dumps(output, indent=4))
    response.headers['Content-Type'] = 'application/json'

    return response, 200

@bp.route('/services/memento/contentdata/')
@bp.route('/services/memento/archivedata/')
@bp.route('/services/memento/originalresourcedata/')
@bp.route('/services/memento/bestimage/')
@bp.route('/services/memento/seeddata/')
def no_urim():
    path = request.url_rule.rule
    return """WARNING: no URI-M submitted, please append a URI-M to {}
Example: {}/https://web.archive.org/web/20180515130056/http://www.cs.odu.edu/~mln/""".format(path, path), 200

@bp.route('/services/memento/contentdata/<path:subpath>')
def textinformation_endpoint(subpath):

    module_logger.debug("full path: {}".format(request.full_path))

    # because Flask trims off query strings
    urim = extract_urim_from_request_path(request.full_path, '/services/memento/contentdata/')

    preferences = {}
    module_logger.debug("URI-M for content data is {}".format(urim))
    return handle_errors(contentdata, urim, preferences)

@bp.route('/services/memento/bestimage/<path:subpath>')
def bestimage_endpoint(subpath):

    # because Flask trims off query strings
    urim = extract_urim_from_request_path(request.full_path, '/services/memento/bestimage/')

    prefs = {}
    prefs['datauri_image'] = 'no'

    if 'Prefer' in request.headers:

        preferences = request.headers['Prefer'].split(',')

        for pref in preferences:
            key, value = pref.split('=')
            prefs[key] = value.lower()

    return handle_errors(bestimage, urim, prefs)

@bp.route('/services/memento/imagedata/<path:subpath>')
def imagedata_endpoint(subpath):

    # because Flask trims off query strings
    urim = extract_urim_from_request_path(request.full_path, '/services/memento/bestimage/')

    prefs = {}

    # if 'Prefer' in request.headers:

    #     preferences = request.headers['Prefer'].split(',')

    #     for pref in preferences:
    #         key, value = pref.split('=')
    #         prefs[key] = value.lower()

    return handle_errors(imagedata, urim, prefs)

@bp.route('/services/memento/archivedata/<path:subpath>')
def archivedata_endpoint(subpath):
    # because Flask trims off query strings
    urim = extract_urim_from_request_path(request.full_path, '/services/memento/archivedata/')

    prefs = {}
    prefs['datauri_favicon'] = 'no'

    if 'Prefer' in request.headers:

        preferences = request.headers['Prefer'].split(',')

        for pref in preferences:
            key, value = pref.split('=')
            prefs[key] = value.lower()

    return handle_errors(archivedata, urim, prefs)

@bp.route('/services/memento/originalresourcedata/<path:subpath>')
def originaldata_endpoint(subpath):
    # because Flask trims off query strings
    urim = extract_urim_from_request_path(request.full_path, '/services/memento/originalresourcedata/')
    prefs = {}
    prefs['datauri_favicon'] = 'no'

    if 'Prefer' in request.headers:

        preferences = request.headers['Prefer'].split(',')

        for pref in preferences:
            key, value = pref.split('=')
            prefs[key] = value.lower()

    return handle_errors(originaldata, urim, prefs)

@bp.route('/services/memento/seeddata/<path:subpath>')
def seeddata_endpoint(subpath):
    urim = extract_urim_from_request_path(request.full_path, '/services/memento/seeddata/')
    prefs = {}

    return handle_errors(seeddata, urim, prefs)
