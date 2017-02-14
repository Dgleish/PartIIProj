from random import randint, seed, random

from sortedcontainers import SortedList

from crdt.base_ordered_list import BaseOrderedList, Node
from crdt.crdt_exceptions import VertexNotFound
from crdt.path_id import PathId

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

        head_id = PathId(None, 1)
        end_id = PathId(None, ((1 << self.base) - 1))
        self.head = Node((None, head_id), flag='START')
        end_node = Node((None, end_id), flag='END')
        self.head.next_node = end_node

        self.nodes = {self.head.id: self.head, end_id: end_node}

        self.ids = SortedList([head_id, end_id])

        self.alloc_strategy = {1: 1, -1: 0}


    def alloc_hash(self, depth):
        seed(1324515 * depth)
        return random() < 0.5

    def get_initial_cursor(self):
        return self.head.id

    def alloc(self, left_id: PathId, right_id: PathId):
        depth = 0
        interval = 0
        while interval < 1:
            depth += 1
            r = right_id.prefix(depth)
            l = left_id.prefix(depth)
            interval = (r - l) - 1
        step = min(self.boundary, interval)
        add_val = randint(1, step)
        if depth not in self.alloc_strategy:
            self.alloc_strategy[depth] = self.alloc_hash(depth)
        if self.alloc_strategy[depth]:
            # logging.debug('using strategy boundary {}'.format('plus'))
            id = PathId(self.puid, left_id.prefix(depth) + add_val, depth)
        else:
            # logging.debug('using strategy boundary {}'.format('minus'))
            id = PathId(self.puid, right_id.prefix(depth) - add_val, depth)

        return id

    def _lookup(self, id) -> Node:
        # special condition for representation of start node
        if id is None:
            return self.head

        # will throw KeyError if not found
        try:
            node = self.nodes[id]
            return node
        except KeyError:
            raise VertexNotFound(id)

    def _approx_lookup(self, id: PathId) -> Node:
        # binary search ids
        i = self.ids.bisect_left(id)
        prev_id = self.ids[i - 1]
        return self._lookup(prev_id)

    def _get_node(self, left_id):
        try:
            left_node = self._lookup(left_id)
        except VertexNotFound as e:
            left_node = self._approx_lookup(left_id)
        return left_node

    def _insert(self, left_id, a, new_id, left_node, right_node):
        # insert new node with this id
        new_node = Node((a, new_id))
        left_node.next_node = new_node
        new_node.next_node = right_node
        new_node.prev_node = left_node
        if right_node is not None:
            right_node.prev_node = new_node

        # yay log search
        left_loc = self.ids.index(left_node.id)
        self.ids.add(new_id)
        self.nodes[new_id] = new_node
        # MUST RETURN ID AS WE JUST GENERATED IT
        return left_id, (a, new_id)

    def insert(self, left_id, new_vertex):
        a, vertex_id = new_vertex
        # lookup node
        left_node = self._get_node(left_id)
        # get next node
        right_node = left_node.next_node
        # allocate id between them
        new_id = self.alloc(left_id, right_node.id)
        return self._insert(left_id, a, new_id, left_node, right_node)

    def insert_remote(self, left_id, new_vertex):
        a, vertex_id = new_vertex
        # we've inserted this before
        if vertex_id in self.nodes:
            return left_id, new_vertex
        # lookup node
        left_node = self._get_node(left_id)
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
        return self._insert(left_id, a, new_id, left_node, right_node)

    def _remove_node(self, id):
        del self.nodes[id]
        self.ids.remove(id)

    def delete(self, id):
        try:
            node = self._lookup(id)
            if node.start_node:
                return id

            pred_id = self.predecessor(id)
            prev = node.prev_node
            prev.next_node = node.next_node
            succ = node.next_node
            succ.prev_node = prev
            self._remove_node(id)
            return pred_id
        except VertexNotFound as e:
            return id

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

    def successor(self, id, only_active=False):
        curr = self._lookup(id)
        if curr.end_node:
            return curr.id
        succ = curr.next_node

        # if reached the end, return last id again
        if succ is None or (only_active and succ.end_node):
            return id

        return succ.id

    def predecessor(self, id, only_active=False):
        pred = self._lookup(id).prev_node

        # if reached the beginning, return id for start of list (= None)
        if pred is None or pred.start_node:
            return self.head.id

        return pred.id
