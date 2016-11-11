class VertexNotFound(Exception):
    def __init__(self, vertex):
        self.vertex = vertex

    def __str__(self):
        return 'VertexNotFound: {}'.format(repr(self.vertex))
