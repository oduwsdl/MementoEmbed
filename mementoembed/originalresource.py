
class OriginalResource:

    def __init__(self, memento, http_cache):
        self.memento = memento
        self.http_cache = http_cache

    @property
    def domain(self):
        pass

    @property
    def uri(self):
        return self.memento.original_uri()

    @property
    def favicon(self):
        pass

    @property
    def link_status(self):
        pass