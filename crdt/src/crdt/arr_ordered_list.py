from crdt.base_ordered_list import BaseOrderedList, Node
from crdt.crdt_exceptions import VertexNotFound


class ArrOrderedList(BaseOrderedList):
    def __init__(self, ):
        self.nodes = [Node('START'), Node('END')]

    def _lookup(self, clock):
        if clock is None:
            return (self.nodes[0], 0, 0)

        el_index = 0
        for i in range(1, len(self.nodes) - 1):
            if not self.nodes[i].deleted:
                el_index += 1
            if self.nodes[i].clock == clock:
                return (self.nodes[i], i, el_index)

        raise VertexNotFound(clock)

    def successor(self, clock, only_active=False):
        looked_up = self._lookup(clock)

        node, index, _ = looked_up
        # index in [0,len(self.nodes)-2]
        index += 1
        succ = self.nodes[index]
        if only_active:
            while succ.deleted and index < len(self.nodes) - 1:
                index += 1
                succ = self.nodes[index]

        if succ.end_node:
            return clock

        return succ.clock

    def predecessor(self, clock, only_active=False):
        looked_up = self._lookup(clock)
        node, index, _ = looked_up
        index -= 1
        pred = self.nodes[index]

        if only_active:
            while pred.deleted and index > 0:
                index -= 1
                pred = self.nodes[index]

        if pred.start_node:
            return None

        return pred.clock

    def insert(self, left_clock, new_vertex):
        # find where to insert
        (left_node, index, _) = self._lookup(left_clock)
        # create new node
        new_node = Node(new_vertex)
        self.nodes.insert(index + 1, new_node)

    def delete(self, clock):
        (node, index, _) = self._lookup(clock)
        node.deleted = True
        return clock

    def get_repr(self, cursor):
        list_repr = [x.contents[0] for x in filter(
            lambda y: not y.deleted, self.nodes[1:-1]
        )]
        _, _, el_index = self._lookup(cursor)
        return ''.join(list_repr), el_index

    def get_detailed_repr(self):
        return ''.join(map(lambda x: '(D{}D)'.format(str(x.contents)) if x.deleted
        else str(x.contents), self.nodes[1:-1]))
