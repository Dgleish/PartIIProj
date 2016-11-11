# this relies on reliable inorder message delivery
# -> clock values are increasing

import logging
from logging.config import fileConfig

fileConfig('../logging_config.ini')
logger = logging.getLogger(__name__)

class ListCRDT(object):
    def __init__(self, uid, olist):
        self.olist = olist
        # clock will be local clock , UID pair
        self.clock = '1:' + uid
        self.uid = uid
        self.cursor = None

    def update_clock(self, t):
        old = int(self.clock.split(':')[0])
        new_clk = max(old, int(t.split(':')[0]) + 1)
        self.clock = '{}:{}'.format(new_clk,self.uid)

    def increment_clock(self):
        self.clock = '{}:{}'.format(
            str(int(self.clock.split(':')[0])+1),
            self.uid
        )

    def add_right_local(self, a):
        t = self.clock
        op_performed = ('ins', self.cursor, (a, t))
        self.add_right(self.cursor, (a, t))
        self.increment_clock()
        self.cursor = (a, t)
        return op_performed

    def add_right_remote(self, vertex, (a,t)):
        self.add_right(vertex, (a, t))
        self.update_clock(t)

    def add_right(self, vertex, (a, t)):
        l = vertex
        r = self.olist.successor(vertex)
        while r != l and t < r[1]:
            l, r = r, self.olist.successor(r)
        return self.olist.insert(l, (a, t))


    def delete(self, vertex):
        try:
            self.olist.delete(vertex)
        except KeyError:
            pass
    def pretty_print(self):
        return self.olist.get_repr()

    def detail_print(self):
        return self.olist.get_detailed_repr() + ', cursor:' + str(self.cursor)

    def shift_cursor_right(self):
        # need a way to stop at end of the list
        self.cursor = self.olist.successor(self.cursor)

    def shift_cursor_left(self):
        # uh oh going to need predecessor
        self.cursor = self.olist.predecessor(self.cursor)
