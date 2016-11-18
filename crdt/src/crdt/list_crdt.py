# this relies on reliable inorder message delivery
# -> clock values are increasing
import logging
from logging.config import fileConfig

from crdt_clock import CRDTClock
from crdt_exceptions import MalformedOp, UnknownOp, VertexNotFound
from crdt_ops import (CRDTOp, RemoteCRDTOp, CRDTOpAddRightLocal,
                      CRDTOpAddRightRemote, CRDTOpDeleteLocal, CRDTOpDeleteRemote)

fileConfig('../logging_config.ini')


class ListCRDT(object):
    def __init__(self, uid, olist):
        self.olist = olist
        self.clock = CRDTClock(uid)
        self.uid = uid
        self.cursor = None

    def can_perform_op(self, op):
        # check if the incoming operation's clock is no more than one ahead of ours
        # otherwise its out of order and gets held back
        if isinstance(op, RemoteCRDTOp):
            return self.clock.can_do(op.clock)
        else:
            return True

    def perform_op(self, op):
        # call the relevant method based on what operation it is
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

    def add_right_local(self, op):
        a = op.atom
        cl = self.clock
        # insert the specified element to the right of the current cursor with the current clock value
        left_clock, vertex_added = self._add_right(self.cursor, (a, cl))
        self.clock.increment()
        self.cursor = cl
        return CRDTOpAddRightRemote(left_clock, vertex_added)

    def add_right_remote(self, op):
        left_clock = op.clock
        vertex_to_add = op.vertex_to_add
        _, cl = vertex_to_add
        self._add_right(left_clock, vertex_to_add)
        self.clock.update(cl)
        return None

    def _add_right(self, left_clock, (a, t)):
        l_cl = left_clock
        r_cl = self.olist.successor(left_clock)
        # determine where to insert after specified element (gives total ordering)
        while r_cl != l_cl and t < r_cl:
            l_cl, r_cl = r_cl, self.olist.successor(r_cl)

        if r_cl != t:
            self.olist.insert(l_cl, (a, t))
        return left_clock, (a, t)

    def delete_remote(self, op):
        clock = op.clock
        try:
            self.olist.delete(clock)
        except VertexNotFound as e:
            logging.warn('Failed to delete {}, {}'.format(clock, e))
        return None

    # noinspection PyUnusedLocal
    def delete_local(self, op):
        t = self.cursor
        self.olist.delete(t)
        self.shift_cursor_left()
        return CRDTOpDeleteRemote(t)

    def pretty_print(self):
        return self.olist.get_repr()

    def detail_print(self):
        return self.olist.get_detailed_repr() + ', cursor:' + str(self.cursor)

    def shift_cursor_right(self):
        # need a way to stop at end of the list
        self.cursor = self.olist.successor(self.cursor)

    def shift_cursor_left(self):
        self.cursor = self.olist.predecessor(self.cursor)
