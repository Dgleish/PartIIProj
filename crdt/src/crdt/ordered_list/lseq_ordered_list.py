from random import randint, seed, random
from typing import Any

from sortedcontainers import SortedList

from crdt.clock_id import ClockID
from crdt.crdt_exceptions import VertexNotFound
from crdt.ordered_list.base_ordered_list import BaseOrderedList, Node
from crdt.path_id import PathId


def alloc_hash(depth):
    seed(1324515 * depth)
    return random() < 0.5


class LSEQOrderedList(BaseOrderedList):
    """
        A variable-size identifier method of OrderedList
        That uses sub-linear memory at the expense of
        slower operations (no tombstoning)
    """

    def __init__(self, puid):
        super().__init__(puid)
        self.boundary = 10
        self.base = 5

        head_id = PathId(None, None, 1)
        end_id = PathId(None, None, ((1 << self.base) - 1))
        self.head = Node((None, head_id), flag='START')
        end_node = Node((None, end_id), flag='END')
        self.head.next_node = end_node

        self.nodes = {self.head.id: self.head, end_id: end_node}

        self.ids = SortedList([head_id, end_id])

        self.alloc_strategy = {}

    def start_of_list_check(self, id: PathId):
        return id.num == 1

    def __len__(self):
        return sum(n.id.get_num_bits() for n in self.nodes.values())

    def get_initial_cursor(self):
        return self.head.id

    def alloc(self, left_id: PathId, right_id: PathId, clock: ClockID):
        depth = 0
        interval = 0
        # work out how many ids lie between left_id and right_id and at what depth
        while interval < 1:
            depth += 1
            r = right_id.prefix(depth)
            l = left_id.prefix(depth)
            interval = (r - l) - 1
        # choose random number to allocate id in the interval
        step = min(self.boundary, interval)
        add_val = randint(1, step)

        # LSEQ strategy
        if depth not in self.alloc_strategy:
            self.alloc_strategy[depth] = alloc_hash(depth)
        if self.alloc_strategy[depth]:
            vertex_id = PathId(self.puid, clock, left_id.prefix(depth) + add_val, depth)
        else:
            vertex_id = PathId(self.puid, clock, right_id.prefix(depth) - add_val, depth)

        return vertex_id

    def _lookup(self, vertex_id: PathId) -> Node:
        # will throw KeyError if not found
        try:
            node = self.nodes[vertex_id]
            return node
        except KeyError:
            raise VertexNotFound(vertex_id)

    def _approx_lookup(self, vertex_id: PathId) -> Node:
        # binary search ids
        """
        :param vertex_id: vertex id to lookup
        :return: the next smallest id than vertex_id
        """
        i = self.ids.bisect_left(vertex_id)
        assert (i > 0)
        prev_id = self.ids[i - 1]
        return self._lookup(prev_id)

    def _get_node(self, identifier: PathId) -> Node:
        try:
            left_node = self._lookup(identifier)
        except VertexNotFound as e:
            left_node = self._approx_lookup(identifier)
        return left_node

    def _insert(self, left_id, a, new_id, left_node, right_node):
        # insert new node with this id
        new_node = Node((a, new_id))
        left_node.next_node = new_node
        new_node.next_node = right_node
        new_node.prev_node = left_node
        if right_node is not None:
            right_node.prev_node = new_node

        self.ids.add(new_id)
        self.nodes[new_id] = new_node
        return left_id, (a, new_id)

    def insert(self, left_id, new_vertex):
        a, clock = new_vertex
        # lookup node
        left_node = self._get_node(left_id)
        # get next node
        right_node = left_node.next_node
        # allocate id between them
        new_id = self.alloc(left_id, right_node.id, clock)
        return self._insert(left_id, a, new_id, left_node, right_node)

    def insert_remote(self, left_id, new_vertex):
        a, vertex_id = new_vertex

        # we've inserted this before
        if vertex_id in self.nodes:
            # then we want the node before this one for the left_id
            return self.predecessor(new_vertex.id), new_vertex

        # lookup node (or greatest one smaller than it whether it exists or not)
        left_node = self._get_node(vertex_id)

        # get next node
        right_node = left_node.next_node
        # insert new node with this id
        new_id = vertex_id
        l_id = left_node.id
        r_id = right_node.id
        # gives a total ordering so we insert in the same place as all others

        while r_id != l_id and new_id > r_id:
            l_id, r_id = r_id, self.successor(r_id)
        left_node = self._lookup(l_id)
        right_node = self._lookup(r_id)
        return self._insert(left_node.id, a, new_id, left_node, right_node)

    def _remove_node(self, vertex_id):
        del self.nodes[vertex_id]
        self.ids.remove(vertex_id)

    def delete(self, vertex_id) -> (Any, PathId):
        try:
            node = self._lookup(vertex_id)
            if node.start_node:
                return None, vertex_id

            prev = node.prev_node
            prev.next_node = node.next_node
            succ = node.next_node
            succ.prev_node = prev
            self._remove_node(vertex_id)
            return (node.atom, vertex_id), prev.id
        except VertexNotFound as e:
            return None, vertex_id

    def get_repr(self, cursor):
        list_repr = []
        cursor_pos = 0
        cursor_counter = 0
        curr = self.head.next_node
        while curr is not None:
            if curr.atom is not None:
                list_repr.append(curr.atom)
                cursor_counter += 1
            if curr.id == cursor:
                cursor_pos = cursor_counter
            curr = curr.next_node
        if cursor is None:
            cursor_pos = 0
        return ''.join(list_repr), cursor_pos

    def get_detailed_repr(self):
        list_repr = []
        curr = self.head.next_node
        while curr is not None:
            if curr.contents is not None and curr.atom is not None:
                list_repr.append(str(curr.contents))
            curr = curr.next_node
        return ''.join(list_repr)

    def successor(self, vertex_id, only_active=False):
        curr = self._lookup(vertex_id)
        if curr.end_node:
            return curr.id
        succ = curr.next_node

        # if reached the end, return last id again
        if succ is None or (only_active and succ.end_node):
            return vertex_id

        return succ.id

    def predecessor(self, vertex_id, only_active=False):
        pred = self._lookup(vertex_id).prev_node

        # if reached the beginning, return id for start of list (= None)
        if pred is None or pred.start_node:
            return self.head.id

        return pred.id
