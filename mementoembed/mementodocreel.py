import os
import io
import logging
import hashlib
import textwrap

import numpy as np

from PIL import ImageFile, Image, ImageFont, ImageDraw

from .imageselection import generate_images_and_scores
from .mementoresource import memento_resource_factory
from .textprocessing import extract_title, get_sentence_scores_by_readability_and_lede3
from .originalresource import OriginalResource
from .archiveresource import ArchiveResource

module_logger = logging.getLogger('mementoembed.mementoimagereel')

class MementoDocReelGenerationError(Exception):
    pass

class MementoDocReelFolderNotFound(MementoDocReelGenerationError):
    pass

class MementoDocreel:

    def __init__(self, user_agent, working_directory, httpcache):

        self.user_agent = user_agent
        self.working_directory = working_directory
        self.httpcache = httpcache

        # TODO: image size (height, width) defaults


    def generate_docreel(self, urim, duration, imgcountlimit, sentencecountlimit, requested_width, requested_height, fontfile):

        if os.path.isdir(self.working_directory):

            memento = memento_resource_factory(urim, self.httpcache)

            m = hashlib.sha256()
            m.update(urim.encode('utf8'))
            reelfile = "{}/{}.gif".format(self.working_directory, m.hexdigest())

            imagelist = generate_images_and_scores(
                memento.im_urim,
                self.httpcache
            )

            module_logger.debug("imagelist: {}".format(imagelist))

            for imageuri in imagelist:

                imagelist[imageuri]

            if len(imagelist) == 0:
                imagelist = generate_images_and_scores(
                    memento.urim,
                    self.httpcache
                )

            # TODO: what if imagelist is empty?

            memtitle = extract_title(memento.raw_content)

            # get domain name
            originalresource = OriginalResource(memento, self.httpcache)

            # get archive name
            archive = ArchiveResource(urim, self.httpcache)
            archive.name

            # get memento-datetime
            memento.memento_datetime

            # got sentences
            sentencedata = get_sentence_scores_by_readability_and_lede3(memento.raw_content)

            scorelist = []

            for imageuri in imagelist:
                if 'calculated score' in imagelist[imageuri]:
                    scorelist.append( (imagelist[imageuri]["calculated score"], imageuri) )

            if not os.path.exists(reelfile):
                module_logger.info("generating animated GIF of images, output should be in {}".format(reelfile))
              
            imageims = []

            imagecount = 1

            for imageuri in [ i[1] for i in sorted(scorelist, reverse=True) ]:

                r = self.httpcache.get(imageuri)
                ifp = io.BytesIO(r.content)

                imageims.append(
                    Image.open(ifp).convert("RGBA", palette=Image.ADAPTIVE)
                )

                imagecount += 1

                if imagecount > imgcountlimit:
                    break

            toptitlefnt = ImageFont.truetype(fontfile, 18)
            metadatafnt = ImageFont.truetype(fontfile, 14)
            imout = Image.new("RGBA", (requested_width, requested_height), "black")
            imbase = Image.new("RGBA", (requested_width, requested_height), "black")
            d = ImageDraw.Draw(imbase)
            d.text((10, 10), memtitle, font=toptitlefnt, fill=(255, 255, 255, 255) )

            d.text((30, requested_height - 60), "{}@{}".format(originalresource.domain, memento.memento_datetime), font=metadatafnt, fill=(255, 255, 255, 255))
            d.text((30, requested_height - 30), "Preserved by {}".format(archive.name), font=metadatafnt, fill=(255, 255, 255, 255))

            or_favicon_uri = self.httpcache.get(originalresource.favicon)
            ifp = io.BytesIO(or_favicon_uri.content)
            or_favicon_im = Image.open(ifp).convert("RGBA", palette=Image.ADAPTIVE).resize((16, 16), resample=Image.BICUBIC)
            imbase.paste(or_favicon_im, (3, requested_height - 60), )

            module_logger.debug("archive favicon for docreel is {}".format(archive.favicon))

            archive_favicon_uri = self.httpcache.get(archive.favicon, use_referrer=False)
            ifp = io.BytesIO(archive_favicon_uri.content)
            ar_favicon_im = Image.open(ifp).convert("RGBA", palette=Image.ADAPTIVE).resize((16, 16), resample=Image.BICUBIC)
            imbase.paste(ar_favicon_im, (3, requested_height - 30), )

            textims = []
            sentencecount = 1
            sentencefnt = ImageFont.truetype(fontfile, 20)

            for sentenceitem in sentencedata["scored sentences"]:

                text = sentenceitem["text"]
                text = text.replace('\t', ' ').replace('\n', ' ')

                if len(text) > 60:
                    text = '\n'.join(textwrap.wrap(text, width=60))

                sentenceim = imbase.copy()
                d = ImageDraw.Draw(sentenceim)
                module_logger.debug("writing sentence item {}".format(sentenceitem))
                d.text( (20, 60), text, font=sentencefnt, fill=(255, 255, 255, 255) )
                textims.append(sentenceim)
                sentencecount += 1

                if sentencecount > sentencecountlimit:
                    break

            baseims = []

            for i in range(0, max(len(imageims), len(textims))):

                try:
                    baseims.append(imageims[i])
                except IndexError:
                    pass

                try:
                    baseims.append(textims[i])
                except IndexError:
                    pass

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

            durations = [ 1000 ]

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
                durations.append(duration)
                
                for i in range(1, 99, 10):
                    i = i / 100
                    outputims.append( Image.blend(imbase, newim, i))
                    durations.append(duration)

                for i in range(0, 30):
                    outputims.append(newim)
                    durations.append(duration)

                for i in range(1, 99, 10):
                    i = i / 100
                    outputims.append( Image.blend(newim, imbase, i) )
                    durations.append(duration)

            module_logger.debug("saving animated GIF")

            with open(reelfile, 'wb') as outputfp:
                imout.save(
                    outputfp, save_all=True, format="GIF", 
                    append_images=outputims, duration=duration, loop=0
                )

            module_logger.debug("durations: {}".format(durations))

            with open(reelfile, 'rb') as f:
                data = f.read()

            module_logger.info("Docreel generation successful, returning video")

            # TODO: resize to 400x300

            return data

        else:
            msg = "Docreel folder {} not found".format(self.working_directory)
            module_logger.error(msg)
            raise MementoDocReelFolderNotFound(msg)
