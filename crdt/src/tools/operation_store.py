from bisect import bisect_left
from collections import defaultdict

from tools.decorators import synchronized


# noinspection PyArgumentList
def _find_next_biggest(ops, t):
    # binary search variant
    # returns index of first element with timestamp > t or
    # -1 if no such element exists
    t.increment()
    # returns i such that all elements in ops[:i] are < t
    i = bisect_left([op.op_id for op in ops], t)
    if i == len(ops):
        return -1
    return i


# noinspection PyArgumentList
class OperationStore(object):
    def __init__(self, value_store):
        self.ops = defaultdict(value_store)
        if value_store == set:
            self.add = lambda store, x: store.add(x)
        else:
            self.add = lambda store, x: store.append(x)
        # stack of undone things, push and pop between this and the local list of operations
        self.undone_ops = []

    @synchronized
    def undo(self, puid):
        if len(self.ops[puid]) > 0:
            op_to_undo = self.ops[puid].pop()
            # logging.debug('op_to_undo {}'.format(op_to_undo))
            return op_to_undo
        else:
            # nothing to undo
            return None

    @synchronized
    def redo(self, puid):
        if len(self.undone_ops) > 0:
            op_to_redo = self.undone_ops.pop()
            # logging.debug('op_to_redo {}'.format(op_to_redo))
            return op_to_redo
        else:
            # nothing to redo
            return None

    @synchronized
    def clear_undo(self):
        self.undone_ops.clear()

    @synchronized
    def add_op(self, key, op, store_in_undo=False):
        if key is not None:
            if store_in_undo:
                self.undone_ops.append(op)
            else:
                self.add(self.ops[key], op)

    def _get_ops_for_key_after(self, key, timestamp=None):

        if timestamp is None:
            # give all ops if they don't know about a peer yet
            return self.ops[key]
        # for a peer's operations and a timestamp,
        # find first the next operation after the given timestamp
        # then return all elements in that list after and including the found one
        # if no such operation exists, return empty list
        index = _find_next_biggest(self.ops[key], timestamp)
        if index == -1:
            return []
        else:
            return self.ops[key][index:]

    @synchronized
    def determine_ops_after_vc(self, vector_clock):
        ops_to_send = []
        for key in self.ops:
            # ops_to_send += self._get_ops_for_key_after(key, vector_clock.get_clock(key))
            # MEASUREMENTS
            ops_to_send += self.ops[key]
        return ops_to_send

    @synchronized
    def remove_ops_for_key(self, key):
        if key in self.ops:
            del self.ops[key]

    @synchronized
    def get_ops_for_key(self, key):
        return list(self.ops[key])
