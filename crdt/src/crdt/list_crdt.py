# this relies on reliable inorder message delivery
# -> clock values are increasing
import logging
from copy import copy
from logging.config import fileConfig

from crdt_clock import CRDTClock
from crdt_exceptions import MalformedOp, UnknownOp
from crdt_ops import (CRDTOp, CRDTOpAddRightLocal,
                      CRDTOpAddRightRemote, CRDTOpDeleteLocal, CRDTOpDeleteRemote)

fileConfig('../logging_config.ini')


class ListCRDT(object):
    def __init__(self, puid, olist):
        self.olist = olist
        # The clock of the next thing to be inserted locally
        self.clock = CRDTClock(puid)
        self.puid = puid
        # Where to insert or delete the next local operation
        self.cursor = None

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
            return self.delete_local(op)

        elif isinstance(op, CRDTOp):
            raise UnknownOp

        else:
            raise MalformedOp

    def add_right_local(self, op):
        atom = op.atom

        self.clock.increment()

        clock = copy(self.clock)

        # Insert the specified vertex to the right of the current cursor with the current clock value
        left_clock, vertex_added = self._add_right(self.cursor, (atom, clock))

        # Cursor points at vertex we just inserted
        self.cursor = copy(clock)

        # return corresponding remote operation for others to apply
        return CRDTOpAddRightRemote(left_clock, vertex_added, copy(clock)), True

    def add_right_remote(self, op):
        # Clock of vertex to insert on the right of (ie clock to the left)
        left_clock = op.clock
        vertex_to_add = op.vertex_to_add
        _, cl = vertex_to_add

        self._add_right(left_clock, vertex_to_add)

        # Update local clock so that we are not behind anyone else's clock
        self.clock.update(cl)

        return op, False

    def _add_right(self, left_clock, (a, new_cl)):
        l_cl = left_clock
        r_cl = self.olist.successor(left_clock)
        logging.debug('inserting between {} and {}'.format(l_cl, r_cl))
        # Determine where to insert after specified vertex (gives total ordering)
        while r_cl != l_cl and new_cl < r_cl:
            logging.debug('shift shift shift')
            l_cl, r_cl = r_cl, self.olist.successor(r_cl)

        # Is this vertex new to the list?
        if r_cl != new_cl:
            # If so insert it
            self.olist.insert(l_cl, (a, new_cl))
        return left_clock, (a, new_cl)

    def delete_remote(self, op):
        # which element are we deleting?
        clock = copy(op.clock)
        self.olist.delete(clock)

        self.clock.update(clock)

        return op, False

    # noinspection PyUnusedLocal
    def delete_local(self, op):

        self.clock.increment()

        # where is the cursor
        t = self.cursor

        self.olist.delete(t)
        # move the cursor one element to the left
        self.shift_cursor_left()

        # return corresponding remote operation for others to apply
        clock = copy(self.clock)
        return CRDTOpDeleteRemote(t, clock), True

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
        logging.debug('moved cursor {} to {}'.format(lr, self.cursor))

    def shift_cursor_right(self):
        # Need a way to stop at end of the list
        self.cursor = self.olist.successor_active(self.cursor)

    def shift_cursor_left(self):
        self.cursor = self.olist.predecessor_active(self.cursor)
