# this relies on reliable inorder message delivery
# -> clock values are increasing
import logging
from logging.config import fileConfig

from crdt_exceptions import MalformedOp, UnknownOp, VertexNotFound
from crdt_ops import CRDTOp, CRDTOpAddRightLocal, CRDTOpAddRightRemote, CRDTOpDeleteLocal, CRDTOpDeleteRemote

fileConfig('../logging_config.ini')


# logger = logging.getLogger(__name__)


class ListCRDT(object):
    def __init__(self, uid, olist):
        self.olist = olist
        # clock will be local clock , UID pair
        self.clock = '1:' + uid
        self.uid = uid
        self.cursor = None

    def perform_op(self, op):
        if isinstance(op, CRDTOpAddRightLocal):
            return self.add_right_local(op)

        elif isinstance(op, CRDTOpAddRightRemote):
            return self.add_right_remote(op)

        elif isinstance(op, CRDTOpDeleteRemote):
            return self.delete_remote(op)

        elif isinstance(op, CRDTOpDeleteLocal):
            return self.delete_local(op)

        elif isinstance(op, CRDTOp):
            raise UnknownOp

        else:
            raise MalformedOp

    def update_clock(self, t):
        old = int(self.clock.split(':')[0])
        new_clk = max(old, int(t.split(':')[0]) + 1)
        self.clock = '{}:{}'.format(new_clk, self.uid)

    def increment_clock(self):
        self.clock = '{}:{}'.format(
            str(int(self.clock.split(':')[0]) + 1),
            self.uid
        )

    def add_right_local(self, op):
        a = op.atom
        t = self.clock
        left_clock, vertex_added = self._add_right(self.cursor, (a, t))
        self.increment_clock()
        self.cursor = t
        return CRDTOpAddRightRemote(left_clock, vertex_added)

    def add_right_remote(self, op):
        left_clock = op.left_clock
        vertex_to_add = op.vertex_to_add
        _, t = vertex_to_add
        self._add_right(left_clock, vertex_to_add)
        self.update_clock(t)
        # TODO: work out what to return to indicate not to broadcast it
        return None

    def _add_right(self, left_clock, (a, t)):
        l_cl = left_clock
        r_cl = self.olist.successor(left_clock)
        while r_cl != l_cl and t < r_cl:
            l_cl, r_cl = r_cl, self.olist.successor(r_cl)
        if r_cl != t:
            self.olist.insert(l_cl, (a, t))
        return left_clock, (a, t)

    def delete_remote(self, op):
        clock = op.clock
        try:
            self.olist.delete(clock)
            return None
        except VertexNotFound as e:
            logging.warn('Failed to delete {}, {}'.format(clock, e))
            return None

    # noinspection PyUnusedLocal
    def delete_local(self, op):
        t = self.cursor
        try:
            self.olist.delete(t)
            self.shift_cursor_left()
            return CRDTOpDeleteRemote(t)
        except VertexNotFound as e:
            logging.warn('Failed to delete vertex with clock {}, {}'.format(t, e))
            return None

    def pretty_print(self):
        return self.olist.get_repr()

    def detail_print(self):
        return self.olist.get_detailed_repr() + ', cursor:' + str(self.cursor)

    def shift_cursor_right(self):
        # need a way to stop at end of the list
        self.cursor = self.olist.successor(self.cursor)

    def shift_cursor_left(self):
        self.cursor = self.olist.predecessor(self.cursor)
