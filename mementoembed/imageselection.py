import logging
import base64

from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from PIL import ImageFile

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

    image_list = []

    r = http_cache.get(uri)

    soup = BeautifulSoup(r.text, 'html5lib')

    for imgtag in soup.find_all("img"):
    
        imageuri = urljoin(uri, imgtag.get("src"))
        image_list.append(imageuri)
    
    return image_list

def get_best_image(uri, http_cache):

    module_logger.debug("getting the best image for content at URI {}".format(uri))
    
    maxscore = float("-inf")
    max_score_image = None

    imagelist = get_image_list(uri, http_cache)
    imagescores = {}
    start = 0
    N = len(imagelist)

    # TODO: make this value configurable
    while maxscore < 5000:

        for n in range(start, start + 15):

            if n >= N:
                break

            #print("working on image {} of {}".format(n, N))

            imageuri = imagelist[n]

            if imageuri not in imagescores:

                if imageuri[0:5] == "data:":
            
                    ctype = imageuri.split(';')[0].split(':')[1]

                    imagecontent = base64.b64decode(imageuri.split(',')[1])

                else:
 
                    r = http_cache.get(imageuri)

                    ctype = r.headers['content-type']

                    imagecontent = r.content

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

        if n >= N:
            break

        start += 15

    return max_score_image
