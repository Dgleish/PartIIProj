from base_ordered_list import BaseOrderedList
from crdt_exceptions import VertexNotFound


class Node(object):
    def __init__(self, contents, special=False):
        self.contents = None
        self.atom = None
        self.clock = None
        self.start_node = False
        self.end_node = False

        # To identify the beginning and end of the list
        if special:
            if contents == 'START':
                self.start_node = True
            elif contents == 'END':
                self.end_node = True
        else:
            self.contents = contents
            (self.atom, self.clock) = contents

        self.next_node = None
        self.prev_node = None
        # has this vertex been deleted?
        self.deleted = False


class LLOrderedList(BaseOrderedList):
    def __init__(self):
        self.head = Node('START', True)
        self.head.next_node = Node('END', True)
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
        succ = self._lookup(clock).next_node

        # if reached the end, return last clock again
        if succ is None or succ.end_node:
            return clock

        return succ.clock

    def successor_active(self, clock):
        succ = self._lookup(clock).next_node

        while succ is not None and succ.deleted:
            succ = succ.next_node

        # if reached the end, return last clock again
        if succ is None or succ.end_node:
            return clock

        return succ.clock

    def predecessor(self, clock):
        pred = self._lookup(clock).prev_node

        # if reached the beginning, return clock for start of list (= None)
        if pred is None or pred.start_node:
            return None

        return pred.clock

    def predecessor_active(self, clock):
        pred = self._lookup(clock).prev_node

        while pred is not None and pred.deleted:
            pred = pred.prev_node

        # if reached the beginning, return clock for start of list (= None)
        if pred is None or pred.start_node:
            return None

        return pred.clock

    def insert(self, left_clock, new_vertex):

        left_node = self._lookup(left_clock)

        # create node with that data
        new_node = Node(new_vertex)

        # insert after 'left_clock'
        tmp = left_node.next_node
        left_node.next_node = new_node
        new_node.next_node = tmp
        new_node.prev_node = left_node
        if tmp is not None:
            tmp.prev_node = new_node

        # add to nodes lookup table
        _, cl = new_vertex
        self.nodes[cl] = new_node

    def delete(self, clock):
        # mark deleted
        node = self._lookup(clock)
        node.deleted = True
        return node.clock

    # for pretty printing
    def get_repr(self, cursor):
        list_repr = []
        cursor_pos = 0
        cursor_counter = 0
        curr = self.head.next_node
        while curr is not None:
            if (not curr.deleted) and curr.contents is not None:
                list_repr.append(curr.contents[0])
                cursor_counter += 1
            if curr.clock == cursor:
                cursor_pos = cursor_counter
            curr = curr.next_node
        if cursor is None:
            cursor_pos = 0
        return ''.join(list_repr), cursor_pos

    # for debug purposes
    def get_detailed_repr(self):
        list_repr = []
        curr = self.head.next_node
        while curr is not None:
            if curr.contents is not None:
                if curr.deleted:
                    list_repr.append('(!!D{}D!!)'.format(str(curr.contents)))
                else:
                    list_repr.append(str(curr.contents))
            curr = curr.next_node
        return ''.join(list_repr)
