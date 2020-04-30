import logging
import json
import traceback
import pprint

from datetime import datetime

from flask import render_template, request, make_response, Blueprint, current_app

from mementoembed.mementoresource import memento_resource_factory
from mementoembed.originalresource import OriginalResource
from mementoembed.textprocessing import extract_text_snippet, extract_title, \
    get_sentence_scores_by_just_textrank, get_section_scores_by_readability, \
    get_sentence_scores_by_readability_and_textrank, get_sentence_scores_by_readability_and_lede3, \
    TitleExtractionError, SnippetGenerationError
from mementoembed.sessions import ManagedSession
from mementoembed.archiveresource import ArchiveResource
from mementoembed.seedresource import SeedResource
from mementoembed.imageselection import get_best_image, convert_imageuri_to_pngdata_uri, generate_images_and_scores
from mementoembed.version import __useragent__

from .errors import handle_errors
from . import extract_urim_from_request_path
from .. import getURICache

bp = Blueprint('services.memento', __name__)

module_logger = logging.getLogger('mementoembed.services.memento')

def paragraphrank(urim, preferences):

    output = {}

    httpcache = getURICache(urim)

    memento = memento_resource_factory(urim, httpcache)

    output['urim'] = urim
    output['generation-time'] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    scoredata = get_section_scores_by_readability(memento.raw_content)
    output.update(scoredata)

    response = make_response(json.dumps(output, indent=4))
    response.headers['Content-Type'] = 'application/json'
    return response, 200

def sentencerank(urim, preferences):

    output = {}

    httpcache = getURICache(urim)

    memento = memento_resource_factory(urim, httpcache)

    output['urim'] = urim
    output['generation-time'] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    scoredata = {}

    if preferences["algorithm"] == "readability/lede3":
        scoredata = get_sentence_scores_by_readability_and_lede3(memento.raw_content)
    elif preferences["algorithm"] == "readability/textrank":
        scoredata = get_sentence_scores_by_readability_and_textrank(memento.raw_content)
    elif preferences["algorithm"] == "justext/textrank":
        scoredata = get_sentence_scores_by_just_textrank(memento.raw_content)
    else:
        scoredata = get_sentence_scores_by_readability_and_lede3(memento.raw_content)
    
    output.update(scoredata)

    response = make_response(json.dumps(output, indent=4))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Preference-Applied'] = \
        "algorithm={}".format(preferences['algorithm'])

    return response, 200

def contentdata(urim, preferences):

    output = {}

    httpcache = getURICache(urim)

    memento = memento_resource_factory(urim, httpcache)

    output['urim'] = urim
    output['generation-time'] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        output['title'] = extract_title(memento.raw_content)

        if output['title'] == '':
            module_logger.warning("empty title detected for {}, attempting to extract title from non-raw content")
            output['title'] = extract_title(memento.content)
    except TitleExtractionError:
        module_logger.exception("failed to extract title from content for {}, attempting with non-raw content".format(urim))
        output['title'] = extract_title(memento.content)

    try:
        output['snippet'] = extract_text_snippet(memento.raw_content)
    except SnippetGenerationError:
        module_logger.exception("failed to extract snippet from content for {}, attempting with non-raw content".format(urim))
        output['snippet'] = extract_text_snippet(memento.content)

    output['memento-datetime'] = memento.memento_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    response = make_response(json.dumps(output, indent=4))
    response.headers['Content-Type'] = 'application/json'
    return response, 200

def originaldata(urim, preferences):

    output = {}

    httpcache = getURICache(urim)

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

    httpcache = getURICache(urim)

    memento = memento_resource_factory(urim, httpcache)

    module_logger.debug("trying to find best image with {}".format(memento.im_urim))
    best_image_uri = get_best_image(
        memento.im_urim, 
        httpcache,
        current_app.config['DEFAULT_IMAGE_URI']
    )

    if best_image_uri == current_app.config['DEFAULT_IMAGE_URI']:
        module_logger.debug("got back a blank image, trying again with {}".format(memento.urim))
        best_image_uri = get_best_image(
            memento.urim, 
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

    httpcache = getURICache(urim)

    memento = memento_resource_factory(urim, httpcache)

    output = {}

    output['urim'] = urim
    output['processed urim'] = memento.im_urim
    output['generation-time'] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    output['images'] = generate_images_and_scores(memento.im_urim, httpcache)

    scorelist = []
    output["ranked images"] = []

    module_logger.debug("images data structure: {}".format(pprint.pformat(output['images'], indent=4)))

    for imageuri in output['images']:
        module_logger.debug("looking for calculated score in imageuri {}".format(imageuri))
        if output['images'][imageuri] is not None:
            if 'calculated score' in output['images'][imageuri]:

                try:

                    if output['images'][imageuri]['is-a-memento'] == True:
                        # we don't want the live web leaking in
                        scorelist.append( (output['images'][imageuri]["calculated score"], imageuri) )

                except KeyError:
                    module_logger.exception("there was an issue determining if {} was a memento".format(imageuri))
                    continue

    for item in sorted(scorelist, reverse=True):
        output["ranked images"].append(item[1])

    if len(output["ranked images"]) == 0:
        output['images'] = generate_images_and_scores(memento.urim, httpcache)

        scorelist = []
        output["ranked images"] = []

        for imageuri in output['images']:

            if 'calculated score' in output['images'][imageuri]:

                if output['images'][imageuri]['is-a-memento'] == True:
                    # we don't want the live web leaking in
                    scorelist.append( (output['images'][imageuri]["calculated score"], imageuri) )

        for item in sorted(scorelist, reverse=True):
            output["ranked images"].append(item[1])

    response = make_response(json.dumps(output, indent=4))
    response.headers['Content-Type'] = 'application/json'

    return response, 200

def archivedata(urim, preferences):

    httpcache = getURICache(urim)

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

    httpcache = getURICache(urim)

    memento = memento_resource_factory(urim, httpcache)

    sr = SeedResource(memento, httpcache)

    output = {}

    output['urim'] = urim
    output['generation-time'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    output['timemap'] = sr.urit
    output['original-url'] = sr.urir
    output['memento-count'] = sr.mementocount()

    if sr.mementocount() is None:
        output['seeddata-error'] = "There was an issue processing the TimeMap discovered at {}".format(sr.urit)

    if sr.first_mdt() is not None:
        output['first-memento-datetime'] = sr.first_mdt().strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        output['first-memento-datetime'] = None
    
    output['first-urim'] = sr.first_urim()

    if sr.last_mdt() is not None:
        output['last-memento-datetime'] = sr.last_mdt().strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        output['last-memento-datetime'] = None

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

@bp.route('/services/memento/paragraphrank/<path:subpath>')
def paragraphrank_endpoint(subpath):
    module_logger.debug("full path: {}".format(request.full_path))

    # because Flask trims off query strings
    urim = extract_urim_from_request_path(request.full_path, '/services/memento/paragraphrank/')

    preferences = {}
    module_logger.debug("URI-M for readability data is {}".format(urim))
    return handle_errors(paragraphrank, urim, preferences)

@bp.route('/services/memento/sentencerank/<path:subpath>')
def sentencerank_endpoint(subpath):
    module_logger.debug("full path: {}".format(request.full_path))

    # because Flask trims off query strings
    urim = extract_urim_from_request_path(request.full_path, '/services/memento/sentencerank/')

    prefs = {
        "algorithm": "readability/lede3"
    }

    if 'Prefer' in request.headers:

        preferences = request.headers['Prefer'].split(',')

        for pref in preferences:
            key, value = pref.split('=')
            prefs[key] = value.lower()

    module_logger.debug("URI-M for readability data is {}".format(urim))
    return handle_errors(sentencerank, urim, prefs)

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
