from bisect import bisect_left
from collections import defaultdict

from tools.decorators import synchronized


# noinspection PyArgumentList
class OperationStore(object):
    def __init__(self, value_store):
        self.ops = defaultdict(value_store)
        if value_store == set:
            self.add = lambda store, x: store.add(x)
        else:
            self.add = lambda store, x: store.append(x)

    @synchronized
    def add_op(self, key, op):
        self.add(self.ops[key], op)

    def _find_next_biggest(self, ops, t):
        # binary search variant
        # returns index of first element with timestamp > t or
        # -1 if no such element exists
        t.increment()
        # returns i such that all elements in ops[:i] are < t
        i = bisect_left([op.op_id for op in ops], t)
        if i == len(ops):
            return -1
        return i

    def _get_ops_for_key_after(self, key, timestamp=None):

        if timestamp is None:
            # give all ops if they don't know about a peer yet
            return self.ops[key]
        # for a peer's operations and a timestamp,
        # find first the next operation after the given timestamp
        # then return all elements in that list after and including the found one
        # if no such operation exists, return empty list
        index = self._find_next_biggest(self.ops[key], timestamp)
        if index == -1:
            return []
        else:
            return self.ops[key][index:]

    @synchronized
    def determine_ops_after_vc(self, vector_clock):
        ops_to_send = []
        for key in self.ops:
            ops_to_send += self._get_ops_for_key_after(key, vector_clock.get_clock(key))

        return ops_to_send

    @synchronized
    def remove_ops_for_key(self, key):
        if key in self.ops:
            del self.ops[key]

    @synchronized
    def get_ops_for_key(self, key):
        return list(self.ops[key])
