import logging
import base64
import traceback

from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from PIL import ImageFile
from requests.exceptions import RequestException

from .mementoresource import MementoParsingError

module_logger = logging.getLogger('mementoembed.imageselection')

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

def get_best_image(uri, http_cache):

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

                        imagecontent = base64.b64decode(imageuri.split(',')[1])

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
