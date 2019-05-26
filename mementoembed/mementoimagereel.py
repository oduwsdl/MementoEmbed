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

            maxwidth = 0
            maxheight = 0

            # get width, height of largest image to create a base image for others
            for im in baseims:

                module_logger.debug("image size is {}".format(im.size))
                
                if im.size[0] > maxwidth:
                    maxwidth = im.size[0]

                if im.size[1] > maxheight:
                    maxheight = im.size[1]

            # TODO: should we just make a square of the greatest one?

            module_logger.debug("creating a base image of size w:{} x h:{}".format(maxwidth, maxheight))
            
            imout = Image.new("RGBA", (requested_width, requested_height))
            imbase = Image.new("RGBA", (requested_width, requested_height), "black")

            working_ims = []

            for im in baseims:

                im_width = im.size[0]
                im_height = im.size[1]

                # is the width or height greater
                if im_width > im_height:
                    # width is greater

                    if maxwidth < requested_width:
                        newwidth = maxwidth
                        newheight = (maxwidth / im_width) * im_height
                    else:
                        newwidth = requested_width
                        newheight = (requested_width / im_width) * im_height

                elif im_height > im_width:
                    # height is greater

                    if maxheight > requested_height:
                        newheight = maxheight
                        newwidth = (maxheight / im_height) * im_width
                    else:
                        newheight = requested_height
                        newwidth = (requested_height / im_height) * im_width

                elif im_height == im_width:
                    # either works fine

                    if maxwidth < requested_width:
                        newheight = (maxheight / im_height) * im_height
                        newwidth = (maxheight / im_height) * im_width
                    else:
                        newheight = (requested_height / im_height) * im_height
                        newwidth = (requested_height / im_height) * im_width

                im = im.resize((int(newwidth), int(newheight)))

                working_ims.append(im)

            outputims = []

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
                for i in range(1, 99, 5):
                    i = i / 100
                    outputims.append( Image.blend(imbase, newim, i))

                for i in range(0, 30):
                    outputims.append(newim)

                for i in range(1, 99, 5):
                    i = i / 100
                    outputims.append( Image.blend(newim, imbase, i) )

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
