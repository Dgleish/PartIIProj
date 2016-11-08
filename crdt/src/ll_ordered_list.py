from base_ordered_list import BaseOrderedList

class Node(object):
    def __init__(self, contents, special=False):
        self.contents = None
        if special:
            if contents == 'START':
                self.start_node = True
            elif contents == 'END':
                self.end_node = True
        else:
            self.contents = contents
        self.next = None
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
        node = self.nodes[cl]
        return node

    def successor(self, vertex):
        next_node = self._lookup(vertex).next
        return next_node.contents

    def insert(self, vertex, new_vertex):

        left_node = self._lookup(vertex)
        # create node with that data
        new_node = Node(new_vertex)

        # insert after 'vertex'
        tmp = left_node.next
        left_node.next = new_node
        new_node.next = tmp

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
            if (not curr.deleted) and curr.contents is not None:
                list_repr.append(str(curr.contents))
            curr = curr.next
        return ''.join(list_repr)
