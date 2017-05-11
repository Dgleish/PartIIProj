from crdt.identifier import Identifier


class Op(object):
    pass


class LocalOp(Op):
    pass


class RemoteOp(Op):
    def __init__(self, op_id):
        self.vertex_id = None
        self._op_id = op_id

    @property
    def op_id(self) -> Identifier:
        return self._op_id

    def undo(self) -> Op:
        pass


class OpUndo(LocalOp):
    def __init__(self):
        self.op = None
        self.vertex_id = None

    def set_op(self, op: RemoteOp):
        self.op = op
        self.vertex_id = op.vertex_id

    def __str__(self):
        return 'Undo {}'.format(self.op)


class OpRedo(LocalOp):
    def __init__(self):
        self.op = None
        self.vertex_id = None

    def set_op(self, op: RemoteOp):
        self.op = op
        self.vertex_id = op.vertex_id

    def __str__(self):
        return 'Redo {}'.format(self.op)


class OpAddRightLocal(LocalOp):
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


class OpAddRightRemote(RemoteOp):
    def __init__(self, vertex_id, vertex_to_add, op_id):
        super(OpAddRightRemote, self).__init__(op_id)
        self.vertex_id = vertex_id
        self.vertex_to_add = vertex_to_add

    def __getstate__(self):
        return {
            'vertex_id': self.vertex_id,
            'vertex_to_add': self.vertex_to_add,
            'op_id': self._op_id
        }

    def __setstate__(self, state):
        self.vertex_id = state['vertex_id']
        self.vertex_to_add = state['vertex_to_add']
        self._op_id = state['op_id']

    def __str__(self):
        return '(AddRightRemote {} {} {})'.format(self.vertex_id, self.vertex_to_add, self._op_id)

    def __repr__(self):
        return self.__str__()


class OpDeleteLocal(LocalOp):
    def __init__(self):
        pass

    def __str__(self):
        return '(DeleteLocal)'

    def __repr__(self):
        return self.__str__()


class CRDTOpDeleteRemote(RemoteOp):
    def __init__(self, to_be_deleted_vertex, op_id):
        super(CRDTOpDeleteRemote, self).__init__(op_id)
        if to_be_deleted_vertex is not None:
            self.vertex_atom, self.vertex_id = to_be_deleted_vertex
        else:
            self.vertex_id = None
            self.vertex_atom = None

    def __getstate__(self):
        return {
            'vertex_id': self.vertex_id,
            'vertex_atom': self.vertex_atom,
            'op_id': self._op_id
        }

    def __setstate__(self, state):
        self.vertex_id = state['vertex_id']
        self.vertex_atom = state['vertex_atom']
        self._op_id = state['op_id']

    def __str__(self):
        return '(DeleteRemote {} {} {})'.format(self.vertex_atom, self.vertex_id, self._op_id)

    def __repr__(self):
        return self.__str__()