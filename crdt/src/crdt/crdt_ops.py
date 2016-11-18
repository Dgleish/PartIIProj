class CRDTOp(object):
    pass


class RemoteCRDTOp(CRDTOp):
    def __init__(self):
        self.clock = None


class CRDTOpAddRightLocal(CRDTOp):
    def __init__(self, atom):
        self.atom = atom

    def __getstate__(self):
        return self.atom

    def __setstate__(self, atom):
        self.atom = atom

    def __str__(self):
        return '(AddRightLocal {})'.format(self.atom)


class CRDTOpAddRightRemote(RemoteCRDTOp):
    def __init__(self, clock, vertex_to_add):
        self.clock = clock
        self.vertex_to_add = vertex_to_add

    def __getstate__(self):
        return {
            'clock': self.clock,
            'vertex_to_add': self.vertex_to_add
        }

    def __setstate__(self, state):
        self.clock = state['clock']
        self.vertex_to_add = state['vertex_to_add']

    def __str__(self):
        return '(AddRightRemote {} {})'.format(self.clock, self.vertex_to_add)


class CRDTOpDeleteLocal(CRDTOp):
    def __init__(self):
        pass

    def __str__(self):
        return '(DeleteLocal)'


class CRDTOpDeleteRemote(RemoteCRDTOp):
    def __init__(self, clock):
        self.clock = clock

    def __getstate__(self):
        return self.clock

    def __setstate__(self, clock):
        self.clock = clock

    def __str__(self):
        return '(DeleteRemote {})'.format(self.clock)
