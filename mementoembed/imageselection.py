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

def get_image_list(uri, http_cache):

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
                imageuri = urljoin(uri, imgtag.get("src"))
                module_logger.debug("adding imageuri {} to list".format(imageuri))
                image_list.append(imageuri)
        except Exception as e:
            module_logger.error("failed to find images in document using BeautifulSoup")
            raise MementoParsingError(
                "failed to find images in document using BeautifulSoup",
                original_exception=e)

    except RequestException:
        module_logger.warn("Failed to download {} for extracing images, skipping...".format(uri))
        module_logger.debug("Failed to download {}, details: {}".format(uri, repr(traceback.format_exc())))
    
    return image_list

def generate_images_and_scores(uri, http_cache, futuressession=None):

    module_logger.debug("generating list of images and computing their scores")

    image_list = get_image_list(uri, http_cache)

    module_logger.debug

    images_and_scores = {}

    N = len(image_list)

    futures = {}
    starttimes = {}
    image_position = {}

    if futuressession is None:
        module_logger.debug("creating FuturesSession for images from uri {}".format(uri))
        futuressession = FuturesSession(session=http_cache)

    timeout = http_cache.timeout # in case we fall into a crawler trap (CNN?)

    working_image_list = []

    for imageuri in image_list:

        if imageuri not in working_image_list:
            working_image_list.append(imageuri)

            if imageuri[0:5] != 'data:':
                module_logger.debug("adding futures request for {}".format(imageuri))
                futures[imageuri] = futuressession.get(imageuri)
                starttimes[imageuri] = datetime.datetime.now()

            image_position[imageuri] = image_list.index(imageuri)

    # working_image_list = deepcopy(image_list)

    def imageuri_generator(imagelist):

        while len(imagelist) > 0:
            yield random.choice(imagelist)

    for imageuri in imageuri_generator(working_image_list):

        n = image_position[imageuri]

        module_logger.debug("looking at image in position {}, URI: {}".format(n, imageuri))

        if imageuri[0:5] == 'data:':

            try:
                datainput = DataURI(imageuri)
                images_and_scores[imageuri] = {}
                images_and_scores[imageuri]['content-type'] = datainput.mimetype
                images_and_scores[imageuri]['magic type'] = magic.from_buffer(datainput.data)
                images_and_scores[imageuri]['imghdr type'] = imghdr.what(None, datainput.data)
                images_and_scores[imageuri].update(scores_for_image(datainput.data, n, N))
            except (binascii.Error, IOError):
                module_logger.exception("cannot process data image URI discovered in base page at {}, skipping...".format(uri))

            working_image_list.remove(imageuri)

        elif imageuri in futures:

            if futures[imageuri].done():
            
                images_and_scores[imageuri] = {}

                module_logger.debug("examining image {}".format(imageuri))

                try:
                    r = futures[imageuri].result()
                except Exception:
                    module_logger.exception(
                        "Failed to download image URI {}, skipping...".format(imageuri)
                    )
                    images_and_scores[imageuri] = "Image could not be downloaded"
                    working_image_list.remove(imageuri)
                    del futures[imageuri]
                    continue

                module_logger.debug("image {} was successfully downloaded with status {}".format(imageuri, r.status_code))

                if r.status_code == 200:

                    module_logger.debug("extracting image content type information from {}".format(imageuri))

                    try:
                        images_and_scores[imageuri]["content-type"] = r.headers['content-type']
                    except KeyError:
                        module_logger.warning(
                            "could not find a content-type for URI {}".format(imageuri)
                        )
                        images_and_scores[imageuri]["content-type"] = "No content type for image"

                    imagecontent = r.content

                    try:
                        images_and_scores[imageuri]["magic type"] = \
                            magic.from_buffer(r.content)
                    except Exception as e:
                        images_and_scores[imageuri]["magic type"] = "ERROR: {}".format(e)

                    images_and_scores[imageuri]["imghdr type"] = \
                        imghdr.what(None, r.content)

                    if 'image/' in images_and_scores[imageuri]["content-type"]:

                        try:
                            module_logger.debug("acquiring scores for image {}".format(imageuri))
                            images_and_scores[imageuri].update(scores_for_image(imagecontent, n, N))

                        except IOError:
                            images_and_scores[imageuri] = None

                        working_image_list.remove(imageuri)
                        del futures[imageuri]

                    elif images_and_scores[imageuri]["imghdr type"] is not None:

                        module_logger.debug("no content-type, so we fall back to imghdr to guess if this URI points to an image: {}".format(imageuri))

                        try:
                            module_logger.debug("acquiring scores for image {}".format(imageuri))
                            images_and_scores[imageuri].update(scores_for_image(imagecontent, n, N))

                        except IOError:
                            images_and_scores[imageuri] = None

                        working_image_list.remove(imageuri)
                        del futures[imageuri]

                    else:
                        images_and_scores[imageuri] = "Content is not an image"
                        working_image_list.remove(imageuri)
                        del futures[imageuri]

                else:
                    images_and_scores[imageuri] = "Image URI {} returned a status of {}, it could not be downloaded".format(imageuri, r.status_code)
                    working_image_list.remove(imageuri)
                    del futures[imageuri]
            
            else:

                module_logger.debug("checking on timeout of image at {}".format(imageuri))

                if (datetime.datetime.now() - starttimes[imageuri]).seconds > timeout:
                    module_logger.warn("could not download image {} within {} seconds, skipping...".format(imageuri, timeout))
                    futures[imageuri].cancel()
                    del futures[imageuri]
                    working_image_list.remove(imageuri)

        else:
            module_logger.error("imageuri {} not found in futures, but yet not removed?".format(imageuri))

    return images_and_scores

def get_best_scoring_image(uri, http_cache, futuressession=None):

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
        max_score_image = sorted(scorelist, reverse=True)[0][1]

    return max_score_image

def get_best_image(uri, http_cache, default_image_uri=None, futuressession=None):

    best_image_uri = get_best_scoring_image(uri, http_cache, futuressession=futuressession)

    if best_image_uri == None:
        if default_image_uri != None:
            best_image_uri = default_image_uri

    return best_image_uri
