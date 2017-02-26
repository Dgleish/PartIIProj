from crdt.crdt_exceptions import VertexNotFound
from crdt.ordered_list.base_ordered_list import BaseOrderedList, Node


class LLOrderedList(BaseOrderedList):
    def __init__(self, puid):
        super().__init__(puid)
        self.head = Node(None, flag='START')
        self.head.next_node = Node(None, flag='END')
        self.nodes = {}

    def __len__(self):
        total_len = sum(len(n.id.value) * 8 for n in self.nodes.values())
        return total_len

    def get_head(self):
        return self.head

    def lookup(self, vertex_id):
        # special condition for representation of start node
        if vertex_id is None:
            return self.head

        # will throw KeyError if not found
        try:
            node = self.nodes[vertex_id]
            return node
        except KeyError:
            raise VertexNotFound(vertex_id)

    def successor(self, vertex_id, only_active=False):
        succ = self.lookup(vertex_id).next_node

        if only_active:
            while succ is not None and succ.deleted:
                succ = succ.next_node

        # if reached the end, return last id again
        if succ is None or succ.end_node:
            return vertex_id

        return succ.id

    def predecessor(self, vertex_id, only_active=False):
        pred = self.lookup(vertex_id).prev_node

        if only_active:
            while pred is not None and pred.deleted:
                pred = pred.prev_node

        # if reached the beginning, return id for start of list (= None)
        if pred is None or pred.start_node:
            return None

        return pred.id

    def insert(self, left_id, new_vertex):

        a, new_id = new_vertex
        l_id = left_id
        r_id = self.successor(left_id)
        # Determine where to insert after specified vertex (gives total ordering)
        while r_id != l_id and new_id < r_id:
            l_id, r_id = r_id, self.successor(r_id)

        # Is this vertex new to the list?
        if r_id != new_id:
            # If so insert it
            left_node = self.lookup(l_id)

            # create node with that data
            new_node = Node(new_vertex)

            # insert after 'left_id'
            tmp = left_node.next_node
            left_node.next_node = new_node
            new_node.next_node = tmp
            new_node.prev_node = left_node
            if tmp is not None:
                tmp.prev_node = new_node

            # add to nodes lookup table
            _, cl = new_vertex
            self.nodes[cl] = new_node
        return left_id, (a, new_id)

    def delete(self, vertex_id):
        # mark deleted
        node = self.lookup(vertex_id)
        node.deleted = True
        prev_node = self.lookup(self.predecessor(vertex_id, only_active=True))
        return node.atom, prev_node.id

    # for pretty printing
    def get_repr(self, cursor):
        list_repr = []
        cursor_pos = 0
        cursor_counter = 0
        curr = self.head.next_node
        while curr is not None:
            if (not curr.deleted) and curr.contents is not None:
                list_repr.append(curr.atom)
                cursor_counter += 1
            if curr.id == cursor:
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
