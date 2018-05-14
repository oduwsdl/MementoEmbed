
class Surrogate:
"""
    Surrogate generates and stores all information about surrogates
    related to content, uri, and response_headers.
"""

    def __init__(self, uri, content, response_headers):

        self.uri = uri
        self.content = content
        self.response_headers = response_headers


    @property
    def text_snippet(self, selectionMethod="MetadataThenLede3"):
        return content[0:10]

    @property
    def striking_image(self, selectionMethod="Largest"):
        return "noimage"
