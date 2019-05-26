import logging
import base64
import traceback
import io
import sys

import cairosvg
import magic
import imghdr

from base64 import binascii

from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from PIL import ImageFile, Image
from requests.exceptions import RequestException

from .mementoresource import MementoParsingError

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

def generate_images_and_scores(uri, http_cache):

    module_logger.debug("generating list of images and computing their scores")

    image_list = get_image_list(uri, http_cache)

    module_logger.debug

    images_and_scores = {}

    N = len(image_list)
    n = 0

    for imageuri in image_list:

        n += 1
        
        images_and_scores[imageuri] = {}

        module_logger.debug("examining image {}".format(imageuri))

        try:
            r = http_cache.get(imageuri)
        except RequestException:
            module_logger.warning(
                "Failed to download image URI {}, skipping...".format(imageuri)
            )
            images_and_scores[imageuri] = "Image could not be downloaded"
            continue

        module_logger.debug("image {} was successfully downloaded with status {}".format(imageuri, r.status_code))

        if r.status_code == 200:

            try:

                ctype = r.headers['content-type']
                imagecontent = r.content
                images_and_scores[imageuri]["content-type"] = ctype
                images_and_scores[imageuri]["magic type"] = \
                    magic.from_buffer(r.content)
                images_and_scores[imageuri]["imghdr type"] = \
                    imghdr.what(None, r.content)

            except KeyError:
                module_logger.warning(
                    "could not find a content-type for URI {}".format(imageuri)
                )
                images_and_scores[imageuri] = "No content type for image"
                continue

            if 'image/' in ctype:

                try:
                    
                    p = ImageFile.Parser()
                    p.feed(imagecontent)
                    p.close()

                    width, height = p.image.size
                    h = p.image.histogram().count(0)

                    images_and_scores[imageuri]['width'] = width
                    images_and_scores[imageuri]['height'] = height

                    # images_and_scores[imageuri]['histogram'] = p.image.histogram()
                    images_and_scores[imageuri]['blank columns in histogram'] = h

                    s = width * height
                    images_and_scores[imageuri]['size in pixels'] = s

                    r = width / height
                    images_and_scores[imageuri]['ratio width/height'] = r

                    images_and_scores[imageuri]['byte size'] = \
                        sys.getsizeof(imagecontent)

                    k1 = 0.1 
                    k2 = 0.4
                    k3 = 10
                    k4 = 0.5

                    score = (k1 * (N - n)) + (k2 * s) - (k3 * h) - (k4 * r)

                    images_and_scores[imageuri]['N'] = N
                    images_and_scores[imageuri]['n'] = n
                    images_and_scores[imageuri]['k1'] = k1
                    images_and_scores[imageuri]['k2'] = k2
                    images_and_scores[imageuri]['k3'] = k3
                    images_and_scores[imageuri]['k4'] = k4

                    images_and_scores[imageuri]['calculated score'] = score

                except IOError:
                    images_and_scores[imageuri] = None

            else:
                images_and_scores[imageuri] = "Content type is not an image"

        else:
            images_and_scores[imageuri] = "Image URI {} returned a status of {}, it could not be downloaded".format(imageuri, r.status_code)

    return images_and_scores

def get_best_scoring_image(uri, http_cache):

    module_logger.debug("getting the best image for content at URI {}".format(uri))
    
    maxscore = float("-inf")
    max_score_image = None

    imagelist = get_image_list(uri, http_cache)
    imagescores = {}
    start = 0
    N = len(imagelist)

    module_logger.debug("there are {} images to review for URI {}".format(N, uri))

    # TODO: make this value configurable
    while maxscore < 5000:

        for n in range(start, start + 15):

            if n >= N:
                break

            imageuri = imagelist[n]

            module_logger.debug("examining image at URI {}".format(imageuri))

            if imageuri not in imagescores:

                try:

                    ctype = ""
                    imagecontent = ""

                    if imageuri[0:5] == "data:":
                
                        ctype = imageuri.split(';')[0].split(':')[1]

                        try:
                            imagecontent = base64.b64decode(imageuri.split(',')[1])
                        except binascii.Error as e:
                            module_logger.exception("failed to process image data at URI {}, skipping...".format(imageuri))
                            continue

                    else:
    
                        r = http_cache.get(imageuri)

                        if r.status_code == 200:

                            try:

                                ctype = r.headers['content-type']
                                imagecontent = r.content
                            
                            except KeyError as e:
                                module_logger.warn("could not find a content-type for URI {}".format(imageuri))

                    if 'image/' in ctype:
    
                        try:
                            score = score_image(imagecontent, n, N)

                            imagescores[imageuri] = score
            
                            if maxscore is None:
                                maxscore = score
                            else:
                                if score > maxscore:
                                    maxscore = score
                                    max_score_image = imageuri

                        except IOError:
                            # if something went wrong with the download
                            # or the image is not identified correctly
                            imagescores[imageuri] = None

                    else:
                        imagescores[imageuri] = None

                except RequestException as e:
                    module_logger.warning("Failed to download image URI {}, skipping...".format(imageuri))
                    module_logger.debug("Failed to download image URI {}, details: {}".format(imageuri, e))

        if n >= N:
            break

        start += 15

    return max_score_image

def get_best_image(uri, http_cache, default_image_uri=None):

    best_image_uri = get_best_scoring_image(uri, http_cache)

    if best_image_uri == None:
        if default_image_uri != None:
            best_image_uri = default_image_uri

    return best_image_uri
