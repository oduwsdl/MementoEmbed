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
            self._thumbnail_width = "auto"
        else:
            try:
                self._thumbnail_width = int(value)

            except ValueError:
                raise MementoThumbnailSizeInvalid("Attempting to set a non-integer width for thumbnail")

        if self._thumbnail_width < 0:
            raise MementoThumbnailSizeInvalid("Attempting to set a width of 0 or less for thumbnail")
        elif self._thumbnail_width > 5120:
            raise MementoThumbnailSizeInvalid("Attempting to set a height of greater than 2880 for thumbnail")

    @property
    def height(self):
        return self._thumbnail_height

    @height.setter
    def height(self, value):

        if value == "auto":
            self._thumbnail_height = "auto"
        else:
            try:
                self._thumbnail_height = int(value)

            except ValueError:
                raise MementoThumbnailSizeInvalid("Attempting to set a non-integer height for thumbnail")

        if self._thumbnail_height < 0:
            raise MementoThumbnailSizeInvalid("Attempting to set a height of 0 or less for thumbnail")
        elif self._thumbnail_height > 2880:
            raise MementoThumbnailSizeInvalid("Attempting to set a height of greater than 2880 for thumbnail")

    @property
    def viewport_width(self):
        return self._viewport_width

    @viewport_width.setter
    def viewport_width(self, value):

        if value == "auto":
            self._viewport_width = "auto"
        else:
            try:
                self._viewport_width = int(value)

            except ValueError:
                raise MementoThumbnailViewportInvalid("Attempting to set a non-integer viewport width for thumbnail")

        if self._viewport_width < 0:
            raise MementoThumbnailViewportInvalid("Attempting to set a width of 0 or less for viewport")
        elif self._viewport_width > 5120:
            raise MementoThumbnailViewportInvalid("Attempting to set a width higher than 5120 for viewport")

    @property
    def viewport_height(self):
        return self._viewport_height

    @viewport_height.setter
    def viewport_height(self, value):

        if value == "auto":
            self._viewport_height = "auto"
        else:
            try:
                self._viewport_height = int(value)

            except ValueError:
                raise MementoThumbnailViewportInvalid("Attempting to set a non-integer viewport width for thumbnail")

        if self._viewport_height < 0:
            raise MementoThumbnailViewportInvalid("Attempting to set a height of 0 or less for viewport")
        elif self._viewport_height > 2880:
            raise MementoThumbnailViewportInvalid("Attempting to set a height higher than 2880 for viewport")


    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, value):

        if value == "auto":
            self._timeout = 15
        else:
            try:
                self._timeout = int(value)

            except ValueError:
                raise MementoThumbnailTimeoutInvalid("Attempting to set a non-integer timeout for thumbnail generation")
           
        if self._timeout < 0:
            raise MementoThumbnailTimeoutInvalid("Attempting to set timeout of 0 or less for thumbnail generation")
        elif self._timeout > 300:
            raise MementoThumbnailTimeoutInvalid("Attempting to set a value higher than 5 minutes for thumbnail generation")

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
                "viewport_width={}, viewport_height={}, user_agent={}, "
                "thumbnail_outputfile={}, thumbnail_width={}, thumbnail_height={}".format(
                    self.viewport_width, self.viewport_height, self.user_agent,
                    thumbfile, self.width, self.height))

            try:

                # the beginning of some measure of caching
                # if not os.path.exists(thumbfile):
                p = subprocess.Popen(["node", self.thumbnail_script])
                p.wait(timeout=self.timeout)

                im = Image.open(thumbfile)

                height = self.height
                
                if self.height == "auto" or self.height < self.width:
                    ratio = self.viewport_height / self.viewport_width
                    height = ratio * self.width
                
                # module_logger.debug("image width is {}".format(int(self.width)))
                # module_logger.debug("using height of {}".format(int(height)))

                im.thumbnail(
                    ( int(self.width), int(height) ),
                     Image.ANTIALIAS)

                module_logger.debug("thumbnail images size is {}".format(im.size))

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