from crdt.base_ordered_list import BaseOrderedList, Node
from crdt.crdt_exceptions import VertexNotFound


class ArrOrderedList(BaseOrderedList):
    def __init__(self, puid):
        super().__init__(puid)
        self.nodes = [Node(None, flag='START'), Node(None, flag='END')]

    def _lookup(self, id):
        if id is None:
            return (self.nodes[0], 0, 0)

        el_index = 0
        for i in range(1, len(self.nodes) - 1):
            if not self.nodes[i].deleted:
                el_index += 1
            if self.nodes[i].id == id:
                return (self.nodes[i], i, el_index)

        raise VertexNotFound(id)

    def successor(self, id, only_active=False):
        looked_up = self._lookup(id)

        node, index, _ = looked_up
        # index in [0,len(self.nodes)-2]
        index += 1
        succ = self.nodes[index]
        if only_active:
            while succ.deleted and index < len(self.nodes) - 1:
                index += 1
                succ = self.nodes[index]

        if succ.end_node:
            return id

        return succ.id

    def predecessor(self, id, only_active=False):
        looked_up = self._lookup(id)
        node, index, _ = looked_up
        index -= 1
        pred = self.nodes[index]

        if only_active:
            while pred.deleted and index > 0:
                index -= 1
                pred = self.nodes[index]

        if pred.start_node:
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
            # find where to insert
            (left_node, index, _) = self._lookup(left_id)
            # create new node
            new_node = Node(new_vertex)
            self.nodes.insert(index + 1, new_node)
        return left_id, (a, new_id)

    def delete(self, id):
        (node, index, _) = self._lookup(id)
        node.deleted = True
        return self.predecessor(id)

    def get_repr(self, cursor):
        list_repr = [x.contents[0] for x in filter(
            lambda y: not y.deleted, self.nodes[1:-1]
        )]
        _, _, el_index = self._lookup(cursor)
        return ''.join(list_repr), el_index

    def get_detailed_repr(self):
        return ''.join(map(lambda x: '(D{}D)'.format(str(x.contents)) if x.deleted
        else str(x.contents), self.nodes[1:-1]))
