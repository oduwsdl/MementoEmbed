import os
import io
import logging
import hashlib

import numpy as np

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


    def generate_imagereel(self, urim, duration, countlimit, requested_width, requested_height):

        if os.path.isdir(self.working_directory):

            memento = memento_resource_factory(urim, self.httpcache)

            m = hashlib.sha256()
            m.update(urim.encode('utf8'))
            reelfile = "{}/{}.gif".format(self.working_directory, m.hexdigest())

            imagelist = generate_images_and_scores(
                memento.im_urim, 
                self.httpcache
            )

            # TODO: what if imagelist is empty?

            scorelist = []

            for imageuri in imagelist:

                if imagelist[imageuri] is not None:
                    if 'calculated score' in imagelist[imageuri]:
                        scorelist.append( (imagelist[imageuri]["calculated score"], imageuri) )

            if not os.path.exists(reelfile):
                module_logger.info("generating animated GIF of images, output should be in {}".format(reelfile))
              
            baseims = []

            imagecount = 1

            for imageuri in [ i[1] for i in sorted(scorelist, reverse=True) ]:

                r = self.httpcache.get(imageuri)
                ifp = io.BytesIO(r.content)

                baseims.append( 
                    Image.open(ifp).convert("RGBA", palette=Image.ADAPTIVE)
                )

                imagecount += 1

                if imagecount > countlimit:
                    break
            
            imout = Image.new("RGBA", (requested_width, requested_height), "black")
            imbase = Image.new("RGBA", (requested_width, requested_height), "black")

            working_ims = []

            for im in baseims:

                im_width = im.size[0]
                im_height = im.size[1]

                module_logger.debug("image size is {}".format(im.size))

                if im_width > im_height:
                    newwidth = requested_width
                    newheight = (requested_width / im_width) * im_height
                        
                elif im_height > im_width:
                    newheight = requested_height
                    newwidth = (requested_height / im_height) * im_width

                elif im_height == im_width:
                    newheight = (requested_width / im_width) * im_height
                    newwidth = (requested_height / im_height) * im_width

                module_logger.debug("resizing")

                module_logger.debug("newimage size is {}".format( (int(newwidth), int(newheight)) ))

                im = im.resize((int(newwidth), int(newheight)), resample=Image.BICUBIC)

                working_ims.append(im)

            outputims = []

            module_logger.debug("building animated GIF")

            # Thanks: https://stackoverflow.com/questions/2563822/how-do-you-composite-an-image-onto-another-image-with-pil-in-python
            for im in working_ims:

                # imconv = im.convert("RGBA")

                im_w, im_h = im.size

                newim = imbase.copy()
                bg_w, bg_h = newim.size

                offset = ((bg_w - im_w) // 2, (bg_h - im_h) // 2)

                newim.paste(im, offset)

                outputims.append(imbase)
                # TODO: loop this! also, maybe do increments of 0.01?
                for i in range(1, 99, 10):
                    i = i / 100
                    outputims.append( Image.blend(imbase, newim, i))

                for i in range(0, 30):
                    outputims.append(newim)

                for i in range(1, 99, 10):
                    i = i / 100
                    outputims.append( Image.blend(newim, imbase, i) )

            module_logger.debug("saving animated GIF")

            with open(reelfile, 'wb') as outputfp:
                imout.save(
                    outputfp, save_all=True, format="GIF", 
                    append_images=outputims, duration=duration, loop=0
                )

            with open(reelfile, 'rb') as f:
                data = f.read()

            module_logger.info("Image reel generation successful, returning video")

            return data

        else:
            msg = "Imagereel folder {} not found".format(self.working_directory)
            module_logger.error(msg)
            raise MementoImageReelFolderNotFound(msg)
