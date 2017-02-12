# this relies on reliable inorder message delivery
# -> clock values are increasing
import logging
from copy import copy

from crdt.base_ordered_list import BaseOrderedList
from crdt.crdt_clock import CRDTClock
from crdt.crdt_exceptions import MalformedOp, UnknownOp
from crdt.crdt_ops import (CRDTOp, CRDTOpAddRightLocal,
                           CRDTOpAddRightRemote, CRDTOpDeleteLocal, CRDTOpDeleteRemote)


class ListCRDT(object):
    def __init__(self, puid, olist: BaseOrderedList):
        self.olist = olist
        # The clock of the next thing to be inserted locally
        self.clock = CRDTClock(puid)
        self.puid = puid
        # Where to insert or delete the next local operation
        self.cursor = self.olist.get_initial_cursor()

    def get_clock(self):
        return self.clock

    def perform_op(self, op):
        # Call the relevant method based on what operation it is
        if isinstance(op, CRDTOpAddRightLocal):
            return self.add_right_local(op)

        elif isinstance(op, CRDTOpAddRightRemote):
            return self.add_right_remote(op)

        elif isinstance(op, CRDTOpDeleteRemote):
            return self.delete_remote(op)

        elif isinstance(op, CRDTOpDeleteLocal):
            # doesn't need any information
            return self.delete_local()

        elif isinstance(op, CRDTOp):
            raise UnknownOp

        else:
            raise MalformedOp

    def add_right_local(self, op):
        atom = op.atom

        self.clock.increment()

        clock = copy(self.clock)

        # Insert the specified vertex to the right of the current cursor with the current clock value
        left_clock, vertex_added = self.olist.insert(self.cursor, (atom, clock))
        # Cursor points at vertex we just inserted
        self.cursor = copy(vertex_added[1])

        # return corresponding remote operation for others to apply
        return CRDTOpAddRightRemote(left_clock, vertex_added, clock), True

    def add_right_remote(self, op):
        # Clock of vertex to insert on the right of (ie clock to the left)
        left_clock = op.vertex_id
        vertex_to_add = op.vertex_to_add
        _, cl = vertex_to_add

        self.olist.insert_remote(left_clock, vertex_to_add)

        # Update local clock so that we are not behind anyone else's clock
        self.clock.update(op.op_id)

        return op, False

    def delete_remote(self, op):
        # which element are we deleting?
        clock = copy(op.vertex_id)
        prev = self.olist.delete(clock)

        if clock == self.cursor:
            self.cursor = prev

        self.clock.update(op.op_id)

        return op, False

    def delete_local(self):
        if self.cursor is not None:
            self.clock.increment()

            # where is the cursor
            t = self.cursor

            # update cursor to previous element
            self.cursor = self.olist.delete(t)

            # return corresponding remote operation for others to apply
            clock = copy(self.clock)
            return CRDTOpDeleteRemote(t, clock), True
        else:
            return None, False

    def pretty_print(self):
        return self.olist.get_repr(self.cursor)

    def pretty_cursor(self):
        if self.cursor is None:
            return 0
        else:
            return self.cursor.timestamp

    def detail_print(self):
        return self.olist.get_detailed_repr() + ', cursor:' + str(self.cursor)

    def move_cursor(self, lr):
        if lr == 'Left':
            self.shift_cursor_left()
        elif lr == 'Right':
            self.shift_cursor_right()

    def shift_cursor_right(self):
        # Need a way to stop at end of the list
        self.cursor = self.olist.successor(self.cursor, True)
        logging.debug('cursor is now {}'.format(self.cursor))

    def shift_cursor_left(self):
        self.cursor = self.olist.predecessor(self.cursor, True)
        logging.debug('cursor is now {}'.format(self.cursor))
