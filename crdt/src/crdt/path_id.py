import logging

from crdt.identifier import Identifier


class PathId(Identifier):
    def __init__(self, puid, clocks):
        super().__init__(puid)
        self.clocks = clocks

    def get_length(self):
        return len(self.clocks)

    def get_clock(self, depth, puid=''):
        if self.get_length() < depth:
            return (0, puid)
        return self.clocks[depth - 1]

    def prefix(self, depth, puid):
        if depth <= self.get_length():
            return self.clocks[:depth]
        else:
            out = list(self.clocks)
            while len(out) < depth:
                out += [(0, puid)]
            return out

    def __eq__(self, other):
        return str(self.clocks) == str(other.clocks)

    def __lt__(self, other):
        n = self.get_length()
        m = other.get_length()
        for j in range(1, m + 1):
            logging.debug('j is {}'.format(j))
            if j == n + 1:
                return True
            pj = self.get_clock(j)
            qj = other.get_clock(j)
            logging.debug('{} {}'.format(pj, qj))
            if pj < qj:
                return True
            elif pj != qj:
                return False

    def __hash__(self):
        return hash(str(self.clocks))

    def __str__(self):
        return str(self.clocks)

    def __repr__(self):
        return str(self.clocks)
