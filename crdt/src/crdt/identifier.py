class Identifier(object):
    def __init__(self, puid):
        self._puid = puid

    @property
    def puid(self):
        return self._puid

    def __lt__(self, other):
        return False
