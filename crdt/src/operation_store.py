import logging
from bisect import bisect_left
from collections import defaultdict


class OperationStore(object):
    def __init__(self):
        self.ops = defaultdict(list)

    def add_op(self, op):
        puid = op.op_id.puid
        self.ops[puid].append(op)

    def find_next_biggest(self, ops, t):
        # binary search variant
        # returns index of first element with timestamp > t or
        # -1 if no such element exists
        t.increment()
        # returns i such that all elements in ops[:i] are < t
        i = bisect_left([op.op_id for op in ops], t)
        if i == len(ops):
            return -1
        return i

    # TODO: very testable
    def get_ops_after(self, puid, timestamp=None):

        if timestamp is None:
            # give all ops if they don't know about a peer yet
            return self.ops[puid]
        # for a peer's operations and a timestamp,
        # find first the next operation after the given timestamp
        # then return all elements in that list after and including the found one
        # if no such operation exists, return empty list
        index = self.find_next_biggest(self.ops[puid], timestamp)
        if index == -1:
            return []
        else:
            return self.ops[puid][index:]

    def determine_ops(self, vector_clock):
        ops_to_send = []
        logging.debug("determining ops to send for vc {}".format(vector_clock))

        for puid in self.ops:
            ops_to_send += self.get_ops_after(puid, vector_clock.get_clock(puid))

        return ops_to_send
