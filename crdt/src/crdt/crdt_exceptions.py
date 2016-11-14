# Operation refers to a vertex which doesn't exist yet
class VertexNotFound(Exception):
    def __init__(self, vertex):
        self.vertex = vertex

    def __str__(self):
        return 'VertexNotFound: {}'.format(repr(self.vertex))


# Operation object has the wrong type
class MalformedOp(Exception):
    def __init__(self, op):
        self.op = op

    def __str__(self):
        return 'Malformed operation: {}'.format(repr(self.op))


# Operation is of the right type, but unrecognized
class UnknownOp(Exception):
    def __init__(self, op):
        self.op = op

    def __str__(self):
        return 'Unknown operation {}'.format(repr(self.op))
