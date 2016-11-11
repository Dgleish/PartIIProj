from base_ordered_list import BaseOrderedList
from crdt_exceptions import VertexNotFound

class Node(object):
    def __init__(self, contents, special=False):
        self.contents = None
        if special:
            if contents == 'START':
                self.start_node = True
            elif contents == 'END':
                self.end_node = True
        else:
            self.start_node = False
            self.end_node = False
            self.contents = contents
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


    def _lookup(self, vertex):
        # special condition for representation of start node
        if vertex is None:
            return self.head
        # will throw KeyError if not found
        a, cl = vertex
        try:
            node = self.nodes[cl]
            return node
        except KeyError:
            raise VertexNotFound(vertex)

    def successor(self, vertex):
        next_node = self._lookup(vertex).next
        # if reached the end, return last element again
        if next_node.end_node:
            return vertex
        return next_node.contents

    def predecessor(self, vertex):
        prev_node = self._lookup(vertex).prev
        if prev_node.start_node:
            return vertex

        return prev_node.contents

    def insert(self, vertex, new_vertex):

        left_node = self._lookup(vertex)
        # create node with that data
        new_node = Node(new_vertex)

        # insert after 'vertex'
        tmp = left_node.next
        left_node.next = new_node
        new_node.next = tmp
        new_node.prev = left_node
        if tmp is not None:
            tmp.prev = new_node

        # add to nodes lookup table
        _, cl = new_vertex
        self.nodes[cl] = new_node

    def delete(self, vertex):
        node = self._lookup(vertex)
        node.deleted = True

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
                list_repr.append(str(curr.contents))
            curr = curr.next
        return ''.join(list_repr)
