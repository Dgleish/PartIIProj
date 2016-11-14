class CRDTOp(object):
    pass


# have to convert add right local to remote etc.

class CRDTOpAddRightLocal(CRDTOp):
    def __init__(self, atom):
        self.atom = atom

    def __getstate__(self):
        return self.atom

    def __setstate__(self, atom):
        self.atom = atom

    def __str__(self):
        return '(AddRightLocal {})'.format(self.atom)


class CRDTOpAddRightRemote(CRDTOp):
    def __init__(self, left_clock, vertex_to_add):
        self.left_clock = left_clock
        self.vertex_to_add = vertex_to_add

    def __getstate__(self):
        return {
            'left_clock': self.left_clock,
            'vertex_to_add': self.vertex_to_add
        }

    def __setstate__(self, state):
        self.left_clock = state['left_clock']
        self.vertex_to_add = state['vertex_to_add']

    def __str__(self):
        return '(AddRightRemote {} {})'.format(self.left_clock, self.vertex_to_add)


class CRDTOpDeleteLocal(CRDTOp):
    def __init__(self):
        pass

    def __str__(self):
        return '(DeleteLocal)'


class CRDTOpDeleteRemote(CRDTOp):
    def __init__(self, clock):
        self.clock = clock

    def __getstate__(self):
        return self.clock

    def __setstate__(self, clock):
        self.clock = clock

    def __str__(self):
        return '(DeleteRemote {})'.format(self.clock)
