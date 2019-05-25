import os
import io
import logging
import hashlib

from PIL import ImageFile, Image

from .imageselection import generate_images_and_scores
from .mementoresource import memento_resource_factory

module_logger = logging.getLogger('mementoembed.mementoimagereel')

class MementoImageReelGenerationError(Exception):
    pass

class MementoImageReelFolderNotFound(MementoImageReelGenerationError):
    pass

class MementoImageReel:

    def __init__(self, user_agent, working_directory, httpcache):

        self.user_agent = user_agent
        self.working_directory = working_directory
        self.httpcache = httpcache

        # TODO: image size (height, width) defaults


    def generate_imagereel(self, urim, duration):

        if os.path.isdir(self.working_directory):

            memento = memento_resource_factory(urim, self.httpcache)

            m = hashlib.sha256()
            m.update(urim.encode('utf8'))
            reelfile = "{}/{}.gif".format(self.working_directory, m.hexdigest())

            imagelist = generate_images_and_scores(
                memento.im_urim, 
                self.httpcache
            )

            scorelist = []

            for imageuri in imagelist:
                if 'calculated score' in imagelist[imageuri]:
                    scorelist.append( (imagelist[imageuri]["calculated score"], imageuri) )

            if not os.path.exists(reelfile):
                module_logger.info("generating animated GIF of images, output should be in {}".format(reelfile))
              
            baseims = []

            for imageuri in [ i[1] for i in sorted(scorelist, reverse=True) ]:

                r = self.httpcache.get(imageuri)
                ifp = io.BytesIO(r.content)
                baseims.append( 
                    Image.open(ifp)
                )

            maxwidth = 0
            maxheight = 0

            # 1. get width, height of largest image
            for im in baseims:

                module_logger.debug("image size is {}".format(im.size))
                
                if im.size[0] > maxwidth:
                    maxwidth = im.size[0]

                if im.size[1] > maxheight:
                    maxheight = im.size[1]

            module_logger.debug("creating a base image of size w:{} x h:{}".format(maxwidth, maxheight))
            imout = Image.new("RGB", (maxwidth, maxheight))

            # 2. TODO: create an image of that size as a "fade-in" image

            ims = []

            for im in baseims:
                ims.append(imout)
                ims.append(im)

            with open(reelfile, 'wb') as outputfp:
                imout.save(
                    outputfp, save_all=True, format="GIF", 
                    append_images=ims, duration=duration, loop=0
                )

            with open(reelfile, 'rb') as f:
                data = f.read()

            module_logger.info("Image reel generation successful, returning video")

            return data

        else:
            msg = "Imagereel folder {} not found".format(self.working_directory)
            module_logger.error(msg)
            raise MementoImageReelFolderNotFound(msg)
