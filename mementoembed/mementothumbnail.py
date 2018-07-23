import os
import hashlib
import logging
import subprocess

from PIL import Image

module_logger = logging.getLogger('mementoembed.mementothumbnail')

class MementoThumbnailTimeoutInvalid(ValueError):
    pass

class MementoThumbnailSizeInvalid(ValueError):
    pass

class MementoThumbnailViewportInvalid(ValueError):
    pass

class MementoThumbnailGenerationError(Exception):
    pass

class MementoThumbnailFolderNotFound(MementoThumbnailGenerationError):
    pass

class MementoThumbnail:

    def __init__(self, user_agent, working_directory, thumbnail_script):

        self.user_agent = user_agent
        self.working_directory = working_directory
        self.thumbnail_script = thumbnail_script

        # defaults
        self._viewport_width = 1024
        self._viewport_height = 768

        self._thumbnail_width = 208
        self._thumbnail_height = "auto"

        self._timeout = 30

    @property
    def width(self):
        return self._thumbnail_width

    @width.setter
    def width(self, value):

        if value == "auto":
            self._width = "auto"
        elif type(value) != int:
            raise MementoThumbnailSizeInvalid("Attempting to set a non-integer width for thumbnail")
        elif value < 0:
            raise MementoThumbnailSizeInvalid("Attempting to set a width of 0 or less for thumbnail")
        else:
            self._thumbnail_width = value
    
    @property
    def height(self):
        return self._thumbnail_height

    @height.setter
    def height(self, value):

        if value == "auto":
            self._thumbnail_height = "auto"
        elif type(value) != int:
            raise MementoThumbnailSizeInvalid("Attempting to set a non-integer height for thumbnail")
        elif value <= 0:
            raise MementoThumbnailSizeInvalid("Attempting to set a height of 0 or less for thumbnail")
        else:
            self._thumbnail_height = value

    @property
    def viewport_width(self):
        return self._viewport_width

    @viewport_width.setter
    def viewport_width(self, value):

        if value == "auto":
            self._viewport_width = "auto"
        elif type(value) != int:
            raise MementoThumbnailViewportInvalid("Attempting to set a non-integer viewport width for thumbnail")
        elif value < 0:
            raise MementoThumbnailViewportInvalid("Attempting to set a width of 0 or less for viewport")
        elif value > 5120:
            raise MementoThumbnailViewportInvalid("Attempting to set a width higher than 5120 for viewport")
        else:
            self._viewport_width = value

    @property
    def viewport_height(self):
        return self._viewport_height

    @viewport_height.setter
    def viewport_height(self, value):

        if value == "auto":
            self._viewport_height = "auto"
        elif type(value) != int:
            raise MementoThumbnailViewportInvalid("Attempting to set a non-integer viewport width for thumbnail")
        elif value < 0:
            raise MementoThumbnailViewportInvalid("Attempting to set a height of 0 or less for viewport")
        elif value > 2880:
            raise MementoThumbnailViewportInvalid("Attempting to set a height higher than 2880 for viewport")
        else:
            self._viewport_height = value

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, value):

        if value == "auto":
            self._timeout = 15
        elif type(value) != int:
            raise MementoThumbnailViewportInvalid("Attempting to set a non-integer timeout for thumbnail generation")
        elif value < 0:
            raise MementoThumbnailViewportInvalid("Attempting to set timeout of 0 or less for thumbnail generation")
        elif value > 300:
            raise MementoThumbnailViewportInvalid("Attempting to set a value higher than 5 minutes for thumbnail generation")
        else:
            self._timeout = value

    def generate_thumbnail(self, urim):
        
        if os.path.isdir(self.working_directory):
            
            os.environ['URIM'] = urim
            m = hashlib.sha256()

            m.update(
                '/'.join(
                    [   str(self.viewport_width), 
                        str(self.viewport_height), 
                        str(self.width), 
                        str(self.height), 
                        urim
                    ]
                    ).encode('utf8')
                    )

            thumbfile = m.hexdigest()
            thumbfile = "{}/{}.png".format(self.working_directory, m.hexdigest())

            module_logger.debug("Thumbnail will be stored in {}".format(thumbfile))

            os.environ['THUMBNAIL_OUTPUTFILE'] = thumbfile
            os.environ['USER_AGENT'] = self.user_agent

            os.environ['VIEWPORT_WIDTH'] = str(self.viewport_width)
            os.environ['VIEWPORT_HEIGHT'] = str(self.viewport_height)

            module_logger.debug("Starting thumbnail generation script with: "
                "viewport_width={}, viewport_height={}, user_agent={},"
                "thumbnail_outputfile={}".format(
                    self.viewport_width, self.viewport_height, self.user_agent,
                    thumbfile))

            try:

                # the beginning of some measure of caching
                if not os.path.exists(thumbfile):
                    p = subprocess.Popen(["node", self.thumbnail_script])
                    p.wait(timeout=self.timeout)

                im = Image.open(thumbfile)

                height = self.height
                
                if self.height == "auto":
                    ratio = self.viewport_height / self.viewport_width
                    height = ratio * self.width

                im.thumbnail(
                    (int(self.width), int(height)
                    ), Image.ANTIALIAS)
                im.save(thumbfile)

                with open(thumbfile, 'rb') as f:
                    data = f.read()

                module_logger.info("Thumbnail generation successful, returning image")

                return data

            except subprocess.TimeoutExpired:

                module_logger.exception(
                    "Thumbnail script failed to return after {} seconds".format(self.timeout))
                
                raise MementoThumbnailGenerationError(
                    "Thumbnail script failed to return after {} seconds".format(self.timeout))

        else:
            msg = "Thumbmnail folder {} not found".format(self.working_directory)
            module_logger.error(msg)
            raise MementoThumbnailFolderNotFound(msg)
