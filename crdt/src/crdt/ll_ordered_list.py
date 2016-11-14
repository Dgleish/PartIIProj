from base_ordered_list import BaseOrderedList
from crdt_exceptions import VertexNotFound


class Node(object):
    def __init__(self, contents, special=False):
        self.contents = None
        self.atom = None
        self.clock = None
        if special:
            if contents == 'START':
                self.start_node = True
            elif contents == 'END':
                self.end_node = True
        else:
            self.start_node = False
            self.end_node = False
            self.contents = contents
            self.atom = contents[0]
            self.clock = contents[1]
        self.next = None
        self.prev = None
        self.deleted = False


class LLOrderedList(BaseOrderedList):
    def __init__(self):
        self.head = Node('START', True)
        self.head.next = Node('END', True)
        self.nodes = {}

    def get_head(self):
        return self.head

    def _lookup(self, clock):
        # special condition for representation of start node
        if clock is None:
            return self.head
        # will throw KeyError if not found
        try:
            node = self.nodes[clock]
            return node
        except KeyError:
            raise VertexNotFound(clock)

    def successor(self, clock):
        next_node = self._lookup(clock).next
        # if reached the end, return last element again
        if next_node.end_node:
            return clock

        return next_node.clock

    def predecessor(self, clock):
        prev_node = self._lookup(clock).prev
        # if reached the beginning, return first element again
        if prev_node.start_node:
            return clock

        return prev_node.clock

    # returns args passed
    def insert(self, left_clock, new_vertex):

        left_node = self._lookup(left_clock)
        # create node with that data
        new_node = Node(new_vertex)

        # insert after 'left_clock'
        tmp = left_node.next
        left_node.next = new_node
        new_node.next = tmp
        new_node.prev = left_node
        if tmp is not None:
            tmp.prev = new_node

        # add to nodes lookup table
        _, cl = new_vertex
        self.nodes[cl] = new_node

    def delete(self, clock):
        node = self._lookup(clock)
        node.deleted = True
        return node.contents

    def get_repr(self):
        list_repr = []
        curr = self.head.next
        while curr is not None:
            if (not curr.deleted) and curr.contents is not None:
                list_repr.append(curr.contents[0])
            curr = curr.next
        return ''.join(list_repr)

    def get_detailed_repr(self):
        list_repr = []
        curr = self.head.next
        while curr is not None:
            if curr.contents is not None:
                if curr.deleted:
                    list_repr.append('(DELETED {})'.format(str(curr.contents)))
                else:
                    list_repr.append(str(curr.contents))
            curr = curr.next
        return ''.join(list_repr)