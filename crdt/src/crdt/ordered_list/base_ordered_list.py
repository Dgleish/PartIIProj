from typing import Optional, Any

from crdt.identifier import Identifier


class Node(object):
    def __init__(self, contents, flag=None):
        # To identify the beginning and end of the list
        self.start_node = flag == 'START'  # type: bool
        self.end_node = flag == 'END'  # type: bool
        self.contents = contents
        self.atom = None
        self.id = None
        if contents is not None:
            (self.atom, self.id) = contents

        self.next_node = None
        self.prev_node = None

        self.l = None
        self.r = None

        # has this vertex been deleted?
        self.deleted = False  # type: bool

    def __str__(self):
        return '(\'{}\'|{})'.format(self.atom, self.id)

    def __repr__(self):
        return self.__str__()

    def __lt__(self, other):
        return self.id < other.id

    def __eq__(self, other):
        return self.id == other.id


class BaseOrderedList(object):
    def __init__(self, puid):
        self.puid = puid

    def __len__(self):
        pass

    def _lookup(self, vertex_id):
        pass

    def get(self, vertex_id) -> Optional[Identifier]:
        node = self._lookup(vertex_id)
        if node is None:
            return node
        else:
            return node.id

    def successor(self, vertex_id: Optional[Identifier], only_active=False) -> Identifier:
        """
        Find the vertex in the list after the verte with identifier `id`
        :param vertex_id: The identifier to lookup
        :param only_active: For tombstoning lists, ignore deleted vertices
        """
        pass

    def predecessor(self, vertex_id: Optional[Identifier], only_active=False) -> Identifier:
        """
        Find the vertex in the list before the verte with identifier `id`
        :param vertex_id: The identifier to lookup
        :param only_active: For tombstoning lists, ignore deleted vertices
        """
        pass

    def insert(self, left_id: Optional[Identifier], new_vertex: (Any, Identifier)) -> (
            Optional[Identifier], (Any, Identifier)):
        pass

    def insert_remote(self, left_id, new_vertex):
        return self.insert(left_id, new_vertex)

    def delete(self, vertex_id) -> (Any, Identifier):
        pass

    def get_initial_cursor(self) -> Optional[Identifier]:
        """
            Returns, for a type of ordered list, what the first value of the cursor should be
        """
        return None

    def get_repr(self, cursor: Optional[Identifier]) -> str:
        """
            Returns a nice, readable representation of the list
        :param cursor: The position of the cursor, so we can return the element it points to
            separately
        """
        pass

    def get_detailed_repr(self) -> str:
        """
            Returns a detailed representation of the list, including IDs for all the elements,
            useful for debugging purposes.
        """
        pass

    def start_of_list_check(self, id: Identifier):
        return id is None
