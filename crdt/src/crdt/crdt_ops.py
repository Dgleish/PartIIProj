class CRDTOp(object):
    pass


class RemoteCRDTOp(CRDTOp):
    def __init__(self, op_id):
        self.clock = None
        self._op_id = op_id

    @property
    def op_id(self):
        return self._op_id


class CRDTOpAddRightLocal(CRDTOp):
    def __init__(self, atom):
        self.atom = atom

    def __getstate__(self):
        return self.atom

    def __setstate__(self, atom):
        self.atom = atom

    def __str__(self):
        return '(AddRightLocal {})'.format(self.atom)

    def __repr__(self):
        return self.__str__()


class CRDTOpAddRightRemote(RemoteCRDTOp):
    def __init__(self, clock, vertex_to_add, op_id):
        super(CRDTOpAddRightRemote, self).__init__(op_id)
        self.clock = clock
        self.vertex_to_add = vertex_to_add

    def __getstate__(self):
        return {
            'clock': self.clock,
            'vertex_to_add': self.vertex_to_add,
            'op_id': self._op_id
        }

    def __setstate__(self, state):
        self.clock = state['clock']
        self.vertex_to_add = state['vertex_to_add']
        self._op_id = state['op_id']

    def __str__(self):
        return '(AddRightRemote {} {} {})'.format(self.clock, self.vertex_to_add, self._op_id)

    def __repr__(self):
        return self.__str__()


class CRDTOpDeleteLocal(CRDTOp):
    def __init__(self):
        pass

    def __str__(self):
        return '(DeleteLocal)'

    def __repr__(self):
        return self.__str__()


class CRDTOpDeleteRemote(RemoteCRDTOp):
    def __init__(self, to_be_deleted_clock, op_id):
        super(CRDTOpDeleteRemote, self).__init__(op_id)
        self.clock = to_be_deleted_clock

    def __getstate__(self):
        return {
            'clock': self.clock,
            'op_id': self._op_id
        }

    def __setstate__(self, state):
        self.clock = state['clock']
        self._op_id = state['op_id']

    def __str__(self):
        return '(DeleteRemote {} {})'.format(self.clock, self._op_id)

    def __repr__(self):
        return self.__str__()
