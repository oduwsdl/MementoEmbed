import logging
import base64
import traceback
import io
import sys
import random
import datetime
import imghdr

import cairosvg
import magic
import imagehash

from base64 import binascii
from urllib.parse import urljoin, urlparse
from copy import deepcopy

from bs4 import BeautifulSoup
from PIL import ImageFile, Image
from requests.exceptions import RequestException
from requests import Session
from requests_cache import CachedSession
from requests_futures.sessions import FuturesSession
from datauri import DataURI

from .mementoresource import MementoParsingError
from .sessions import ManagedSession

module_logger = logging.getLogger('mementoembed.imageselection')

def convert_imageuri_to_pngdata_uri(imageuri, httpcache, width, height=None):
    
    # TODO: throw an exception when things go wrong, what could go wrong?
    response = httpcache.get(imageuri)
    imagedata = response.content

    module_logger.debug("image detected as {}".format(magic.from_buffer( imagedata) ))

    if magic.from_buffer( imagedata ) == 'SVG Scalable Vector Graphics image':
        module_logger.debug("converting image at {} from SVG to PNG".format(imageuri))
        imagedata = cairosvg.svg2png( imagedata )
        ifp = io.BytesIO( imagedata )
    else:
        ifp = io.BytesIO(imagedata)

    im = Image.open(ifp)

    im_width, im_height = im.size

    if height is None:
        ratio = im_height / im_width
        height = int(ratio * width)

    im.thumbnail((width, height))

    ofp = io.BytesIO()

    im.save(ofp, format='PNG')

    ofp.seek(0)

    newimagedata = ofp.read()

    b64img = base64.b64encode(newimagedata).decode('utf-8')

    datauri = "data:image/png;base64,{}".format(b64img)

    return datauri

def score_image(imagecontent, n, N):

    p = ImageFile.Parser()
    p.feed( imagecontent )
    p.close()
    
    width, height = p.image.size
    
    # how many blank columns in the histogram, indicating an image with very low complexity
    h = p.image.histogram().count(0)
    
    # image size in pixels
    s = width * height
    
    # image ratio
    r = width / height

    # TODO: make these weights configurable
    # weights
    k1 = 0.1 
    k2 = 0.4
    k3 = 10
    k4 = 0.5

    score = (k1 * (N - n)) + (k2 * s) - (k3 * h) - (k4 * r)
    
    return score

def scores_for_image(imagecontent, n, N):

    imagedata = {}

    p = ImageFile.Parser()
    p.feed(imagecontent)
    p.close()

    width, height = p.image.size
    h = p.image.histogram().count(0)

    imagedata['format'] = p.image.format
    imagedata['mode'] = p.image.mode

    imagedata['width'] = width
    imagedata['height'] = height

    imagedata['blank columns in histogram'] = h

    s = width * height
    imagedata['size in pixels'] = s

    r = width / height
    imagedata['ratio width/height'] = r

    imagedata['byte size'] = \
        sys.getsizeof(imagecontent)

    img = Image.open(io.BytesIO(imagecontent))

    # 16777216 is the maximum number of colors in a JPEG
    colors = img.convert('RGB').getcolors(maxcolors=16777216)

    if colors is not None:
        c = len(colors)
        imagedata['colorcount'] = c
    else:
        imagedata['colorcount'] = 16777216

    imagedata['pHash'] = str(imagehash.phash(img))
    imagedata['aHash'] = str(imagehash.average_hash(img))
    imagedata['dHash_horizontal'] = str(imagehash.dhash(img))
    imagedata['dHash_vertical'] = str(imagehash.dhash_vertical(img))
    imagedata['wHash'] = str(imagehash.whash(img))

    k1 = 0.1 
    k2 = 0.4
    k3 = 10
    k4 = 0.5
    k5 = 10

    score = (k1 * (N - n)) + (k2 * s) - (k3 * h) - (k4 * r) + (k5 * c)

    imagedata['N'] = N
    imagedata['n'] = n
    imagedata['k1'] = k1
    imagedata['k2'] = k2
    imagedata['k3'] = k3
    imagedata['k4'] = k4
    imagedata['k5'] = k5

    imagedata['calculated score'] = score

    return imagedata

def get_image_with_timegate(base_uri, imageuri, http_cache):

    new_imageuri = None

    r = http_cache.get(base_uri)

    try:
        urig = r.links['timegate']['url']
        urir = r.links['original']['url']
    except Exception:
        module_logger.exception("Failed to extract values from link headers from base URI {} -- headers: {}".format(base_uri, r.headers))
        return new_imageuri

    if urir in urig:
        module_logger.info("URI-R of page is in URI-G, replacing with image URI-R")

        image_urig = urig.replace(urir, imageuri)

        module_logger.info("new URI-G is {}".format(image_urig))

        r = http_cache.get(image_urig)

        module_logger.info("status code from URI-G was {}".format(r.status_code))

        if r.status_code == 200:
            module_logger.info("discovered image {} through timegate with a 200 status code".format(r.url))

            if 'memento-datetime' in r.headers:
                module_logger.info("confirmed that image {} is a memento, returning it".format(r.url))
                new_imageuri = r.url

    return new_imageuri

def ignore_image(imgtag, ignoreclasses, ignoreids):

    ignoreImage = False

    html_classes = imgtag.get('class') 
    
    ignoreImage = False
    
    if html_classes is not None:
        for html_class in html_classes:
            if html_class in ignoreclasses:
                return True
    
    html_ids = imgtag.get('id')
    
    if html_ids is not None:
        for html_id in html_ids:
            if html_id in ignoreids:
                return True

    for parent in imgtag.parents:

        html_classes = parent.get('class')

        if html_classes is not None:
            for html_class in html_classes:
                if html_class in ignoreclasses:
                    return True
        
        html_ids = parent.get('id')
        
        if html_ids is not None:
            for html_id in html_ids:
                if html_id in ignoreids:
                    return True

    return ignoreImage

def get_image_list(uri, http_cache, ignoreclasses=[], ignoreids=[], ignore_images=[]):

    module_logger.debug("extracting images from the HTML of URI {}".format(uri))

    image_list = []

    try:
        r = http_cache.get(uri)

        module_logger.debug("content from URI-M: {}".format(r.text))

        try:
            soup = BeautifulSoup(r.text, 'html5lib')
        except Exception as e:
            module_logger.error("failed to open document using BeautifulSoup")
            raise MementoParsingError(
                "failed to open document using BeautifulSoup",
                original_exception=e)

        try:
            for imgtag in soup.find_all("img"):
                
                try:
                    imageuri = urljoin(uri, imgtag.get("src"))

                    if ignore_image(imgtag, ignoreclasses, ignoreids) == False:

                        if imageuri not in ignore_images:
                            module_logger.debug("adding imageuri {} to list".format(imageuri))
                            image_list.append(imageuri)

                except Exception:
                    module_logger.exception("Failed to extract value of src attribute from img tag")

                try:
                    imgdata = imgtag.get("srcset")

                    if ignore_image(imgtag, ignoreclasses, ignoreids) == False:

                        if imgdata is not None:
                            imageuris = [ urljoin(uri, k[0]) for k in [ j.split() for j in [ i.strip() for i in imgdata.split(',') ] ] ]


                            if imageuri not in ignore_images:
                                module_logger.debug("adding imageuri {} to list".format(imageuri))
                                image_list.append(imageuri)

                except Exception:
                    module_logger.exception("Failed to extract value of srcset attribute form img tag")

        except Exception as e:
            module_logger.error("failed to find images in document using BeautifulSoup")
            raise MementoParsingError(
                "failed to find images in document using BeautifulSoup",
                original_exception=e)

    except RequestException:
        module_logger.warn("Failed to download {} for extracing images, skipping...".format(uri))
        module_logger.debug("Failed to download {}, details: {}".format(uri, repr(traceback.format_exc())))
    
    return image_list

def generate_images_and_scores(baseuri, http_cache, futuressession=None, ignoreclasses=[], ignoreids=[], ignore_images=[], datetime_negotiation=True):

    # TODO: this function works, but it is a nightmare at this point - break it up somehow

    module_logger.debug("generating list of images and computing their scores")

    base_image_list = get_image_list(baseuri, http_cache, ignoreclasses=ignoreclasses, ignoreids=ignoreids, ignore_images=ignore_images)

    images_and_scores = {}

    module_logger.debug("found {} images in page".format(len(base_image_list)))

    futures = {}
    starttimes = {}
    image_position = {}

    if futuressession is None:
        module_logger.debug("creating FuturesSession for images from uri {}".format(baseuri))
        futuressession = FuturesSession(session=http_cache)

    timeout = http_cache.timeout # in case we fall into a crawler trap (CNN?)

    working_image_list = []

    for imageuri in base_image_list:

        if 'http://a.fssta.com/content/dam/fsdigital/fscom/BOXING/images/2015/03/16/mitt-romney-evander-holyfield.vresize.1200.675.high.93.jpg' in imageuri:
            module_logger.info("imageuri is clearly in body...")

        if imageuri not in working_image_list:
            working_image_list.append(imageuri)

            if imageuri[0:5] != 'data:':
                module_logger.debug("adding futures request for {}".format(imageuri))
                futures[imageuri] = futuressession.get(imageuri)
                starttimes[imageuri] = datetime.datetime.now()

            image_position[imageuri] = base_image_list.index(imageuri)

    # metadata_image_url, metadata_image_field = get_image_from_metadata(uri, http_cache)
    metadata_images = get_image_from_metadata(baseuri, http_cache)

    module_logger.info("discovered {} images in metadata".format(len(metadata_images)))

    if len(metadata_images) > 0:

        for imageuri in metadata_images.keys():

            if imageuri[0:5] != 'data:':

                if imageuri not in working_image_list:
                    futures[imageuri] = futuressession.get(imageuri)
                    starttimes[imageuri] = datetime.datetime.now()
                    working_image_list.append(imageuri)

    def imageuri_generator(imagelist):

        while len(imagelist) > 0:
            yield random.choice(imagelist)

    def find_image_source(imageuri, metadata_images, base_image_list):

        # if imageuri in metadata_images and imageuri in base_image_list:
        #     return "body and metadata"
        if imageuri in metadata_images:
            return "metadata"
        elif imageuri in base_image_list:
            return "body"
        else:
            module_logger.warning("could not image source: {}".format(imageuri))
            return "unknown"

    for imageuri in imageuri_generator(working_image_list):

        images_and_scores[imageuri] = {}
        image_source = find_image_source(imageuri, list(metadata_images.keys()), base_image_list)
        images_and_scores[imageuri]['source'] = image_source
        images_and_scores[imageuri]['is-a-memento'] = False
        images_and_scores[imageuri]['origin'] = 'page-content'

        if 'metadata' in images_and_scores[imageuri]['source']:
            images_and_scores[imageuri]['source_fields'] = metadata_images[imageuri]

        if imageuri in list(metadata_images.keys()) and image_source == "metadata":
            n = -1
            N = len(base_image_list)
        else:
            n = image_position[imageuri]
            N = len(base_image_list)

        module_logger.debug("looking at image in position {}, URI: {}".format(n, imageuri))

        if imageuri[0:5] == 'data:':

            try:
                datainput = DataURI(imageuri)
                images_and_scores[imageuri]['content-type'] = datainput.mimetype
                images_and_scores[imageuri]['magic type'] = magic.from_buffer(datainput.data)
                images_and_scores[imageuri]['imghdr type'] = imghdr.what(None, datainput.data)
                images_and_scores[imageuri].update(scores_for_image(datainput.data, n, N))

                if 'metadata' in images_and_scores[imageuri]['source']:
                    images_and_scores[imageuri]['source_field'] = metadata_images[imageuri]
                
                images_and_scores[imageuri].update(scores_for_image(datainput.data, n, N))
                
            except Exception as e:
                module_logger.exception("cannot process data image URI {} discovered in base page at {}, skipping...".format(imageuri, baseuri))
                images_and_scores[imageuri]['error'] = repr(e)

            working_image_list.remove(imageuri)

        elif imageuri in futures:

            if futures[imageuri].done():

                module_logger.debug("examining image {}".format(imageuri))

                try:
                    r = futures[imageuri].result()
                except Exception as e:
                    module_logger.exception(
                        "Failed to download image URI {}, skipping...".format(imageuri)
                    )

                    images_and_scores[imageuri]['error'] = repr(e)
                    working_image_list.remove(imageuri)
                    del futures[imageuri]
                    continue

                module_logger.debug("image {} was successfully downloaded with status {}".format(imageuri, r.status_code))

                if r.status_code == 200:

                    module_logger.debug("extracting image content type information from {}".format(imageuri))

                    imagecontent = r.content

                    if 'memento-datetime' in r.headers:
                        images_and_scores[imageuri]['is-a-memento'] = True
                    else:
                        # not all image links get rewritten 
                        new_imageuri = None

                        if datetime_negotiation == True:
                            module_logger.warning("image {} from {} is not a memento, attempting datetime negotiation to find a memento".format(imageuri, baseuri))

                            try:
                                new_imageuri = get_image_with_timegate(baseuri, imageuri, http_cache)
                            except Exception:
                                module_logger.exception("attempt at datetime negotiation failed for image {}".format(imageuri))

                        if new_imageuri is not None:

                            try:

                                r = http_cache.get(new_imageuri)

                                if r.status_code == 200:

                                    # create a new record for the memento
                                    images_and_scores.setdefault(new_imageuri, {})
                                    images_and_scores[new_imageuri] = {}
                                    images_and_scores[new_imageuri]['is-a-memento'] = True

                                    # image_source = find_image_source(new_imageuri, list(metadata_images.keys()), base_image_list)
                                    image_source = images_and_scores[imageuri]['source']
                                    images_and_scores[new_imageuri]['source'] = image_source
                                    images_and_scores[new_imageuri]['origin'] = 'datetime-negotiation'
                                    
                                    if 'metadata' in images_and_scores[new_imageuri]['source']:
                                        images_and_scores[new_imageuri]['source_field'] = metadata_images[imageuri]

                                    # so the rest of the existing code will flow smoothly
                                    working_image_list.append(new_imageuri)
                                    futures[new_imageuri] = None

                                    # remove the old record
                                    del images_and_scores[imageuri]
                                    del futures[imageuri]
                                    working_image_list.remove(imageuri)

                                    imagecontent = r.content
                                    imageuri = new_imageuri
                                
                            except Exception:
                                module_logger.exception("Failed to fetch memento of image {}".format(new_imageuri))


                    try:
                        images_and_scores[imageuri]["content-type"] = r.headers['content-type']
                    except KeyError:
                        module_logger.warning(
                            "could not find a content-type for URI {}".format(imageuri)
                        )
                        # images_and_scores[imageuri]["content-type"] = "No content type for image"
                        images_and_scores[imageuri]['error'] = "No content type for image"

                    try:
                        images_and_scores[imageuri]["magic type"] = \
                            magic.from_buffer(imagecontent)
                    except Exception as e:
                        module_logger.exception("failed to determine magic type of {}".format(imageuri))
                        images_and_scores[imageuri]["magic type"] = "ERROR: {}".format(e)

                    images_and_scores[imageuri]["imghdr type"] = \
                        imghdr.what(None, r.content)

                    if 'image/' in images_and_scores[imageuri]["content-type"]:

                        try:
                            module_logger.debug("acquiring scores for image {}".format(imageuri))
                            images_and_scores[imageuri].update(scores_for_image(imagecontent, n, N))

                        except Exception as e:
                            module_logger.exception(
                                "failed to acquire scores for image with content type {}: {}".format(
                                    images_and_scores[imageuri]['content-type'], imageuri))
                            images_and_scores[imageuri]['error'] = repr(e)

                        working_image_list.remove(imageuri)
                        del futures[imageuri]

                    elif images_and_scores[imageuri]["imghdr type"] is not None:

                        module_logger.debug("no content-type, so we fall back to imghdr to guess if this URI points to an image: {}".format(imageuri))

                        try:
                            module_logger.debug("acquiring scores for image {}".format(imageuri))

                            images_and_scores[imageuri].update(scores_for_image(imagecontent, n, N))

                        except Exception as e:
                            # images_and_scores[imageuri] = None
                            module_logger.exception(
                                "failed to acquire scores for image with content type {}: {}".format(
                                    images_and_scores[imageuri]['imghdr type'], imageuri))
                            images_and_scores[imageuri]['error'] = repr(e)

                        working_image_list.remove(imageuri)
                        del futures[imageuri]

                    else:
                        # images_and_scores[imageuri] = "Content is not an image"
                        images_and_scores[imageuri]['error'] = "Content is not an image"
                        working_image_list.remove(imageuri)
                        del futures[imageuri]

                else:
                    # images_and_scores[imageuri] = "Image URI {} returned a status of {}, it could not be downloaded".format(imageuri, r.status_code)
                    images_and_scores[imageuri]['error'] = "Image URI {} returned a status of {}, it could not be downloaded".format(imageuri, r.status_code)
                    working_image_list.remove(imageuri)
                    del futures[imageuri]
            
            else:

                module_logger.debug("checking on timeout of image at {}".format(imageuri))

                if (datetime.datetime.now() - starttimes[imageuri]).seconds > timeout:
                    module_logger.warn("could not download image {} within {} seconds, skipping...".format(imageuri, timeout))
                    images_and_scores[imageuri]['error'] = "could not download image {} within {} seconds, skipping...".format(imageuri, timeout)
                    futures[imageuri].cancel()
                    del futures[imageuri]
                    working_image_list.remove(imageuri)

        else:
            module_logger.error("imageuri {} not found in futures, but yet not removed?".format(imageuri))
            images_and_scores[imageuri]['error'] = "imageuri {} not found in futures, but yet not removed?".format(imageuri)

    return images_and_scores

def get_image_from_metadata(uri, http_cache):

    metadata_images = {}

    module_logger.info("attempting to retrieve images from metadata of {}".format(uri))

    try:
        r = http_cache.get(uri)

        try:
            soup = BeautifulSoup(r.text, 'html5lib')
        except Exception as e:
            module_logger.error("failed to open document using BeautifulSoup")
            raise MementoParsingError(
                "failed to open document using BeautifulSoup",
                original_exception=e)

        for field in [ "og:image", "twitter:image", "twitter:image:src", "image" ]:

            for attribute in [ "property", "name", "itemprop" ]:

                try:
                    module_logger.info("for url: {} --- bs4 discovered: {}".format(uri, soup.find_all('meta', { attribute: field } )))
                    discovered_fields = soup.find_all('meta', { attribute: field } )

                    #module_logger.debug("discovered {} fields with metadata".format(len(discovered_fields)))
                    #module_logger.debug("discovered fields with metadata: {}".format(discovered_fields[0]))
                    #module_logger.debug("discovered content field in metadata: {}".format(discovered_fields[0]['content']))

                    if len(discovered_fields) > 0:

                        for value_attribute in ['content', 'value']:

                            module_logger.debug("searching for image URL by {} value".format(value_attribute))

                            try:
                                metadata_image_url = discovered_fields[0][value_attribute]
                                metadata_image_url = urljoin( uri, metadata_image_url )
                                metadata_images.setdefault(metadata_image_url, []).append('{}="{}" {}'.format(attribute, field, value_attribute))
                            except KeyError:
                                module_logger.debug("did not find metadata image URL using value attribute {}...".format(value_attribute))

                except (IndexError, TypeError):
                    module_logger.debug("did not find metadata-specified image with attribute {} and field {}, moving on...".format(attribute, field))

    except RequestException:
        module_logger.warn("Failed to download {} for extracing images, skipping...".format(uri))
        module_logger.debug("Failed to download {}, details: {}".format(uri, repr(traceback.format_exc())))
        
    # return metadata_image_url, field
    return metadata_images

def get_best_scoring_image(uri, http_cache, futuressession=None):

    # metadata_image_url, field = get_image_from_metadata(uri, http_cache)
    metadata_images = get_image_from_metadata(uri, http_cache)
    metadata_image_url = None
    if len(metadata_images.keys()) > 0:
        metadata_image_url = list(metadata_images.keys())[0]

    if metadata_image_url is not None:
        
        r = http_cache.get(metadata_image_url)

        if r.status_code == 200:

            module_logger.info("discovered image {} with a 200 status code".format(metadata_image_url))

            if 'memento-datetime' in r.headers:
                module_logger.info("discovered image {} is a memento, returning it".format(metadata_image_url))
                return metadata_image_url

            else:
                # not all image links get rewritten
                # TODO: put this in a function
                module_logger.info("metadata image was discovered as an original resource, attempting datetime negotiation...")

                metadata_image_url = get_image_with_timegate(uri, metadata_image_url, http_cache)

                if metadata_image_url is not None:
                    return metadata_image_url

    scorelist = []

    scoredata = generate_images_and_scores(uri, http_cache, futuressession=futuressession)

    for imageuri in scoredata:

        if scoredata[imageuri] is not None:

            if "calculated score" in scoredata[imageuri]:
                scorelist.append(
                    (
                        scoredata[imageuri]["calculated score"],
                        imageuri
                    )
                )

    max_score_image = None

    if len(scorelist) > 0:
        # max_score_image = sorted(scorelist, reverse=True)[0][1]

        for img in sorted(scorelist, reverse=True):
            imageuri = img[1]

            if 'is-a-memento' in scoredata[imageuri]:

                if scoredata[imageuri]['is-a-memento'] == True:
                    max_score_image = imageuri
                    break

    return max_score_image

def get_best_image(uri, http_cache, default_image_uri=None, futuressession=None):

    best_image_uri = get_best_scoring_image(uri, http_cache, futuressession=futuressession)

    if best_image_uri == None:
        if default_image_uri != None:
            best_image_uri = default_image_uri

    module_logger.info("returning best image URL of {}".format(best_image_uri))

    return best_image_uri
