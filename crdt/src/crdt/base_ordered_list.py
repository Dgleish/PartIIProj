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

    @staticmethod
    def missing_predecessor(root, id, ancestor=None):
        if root is None:
            return ancestor
        if root.id < id:
            return Node.missing_predecessor(root.r, id, root)
        else:
            return Node.missing_predecessor(root.l, id, ancestor)

    @staticmethod
    def insert(root, val):
        if root is None:
            return
        elif root.id == val.id:
            return
        elif val.id < root.id:
            if root.l is None:
                root.l = val
            else:
                Node.insert(root.l, val)
        else:
            if root.r is None:
                root.r = val
            else:
                Node.insert(root.r, val)


class BaseOrderedList(object):
    def __init__(self, puid):
        self.puid = puid

    def successor(self, id, only_active=False) -> Identifier:
        pass

    def predecessor(self, id, only_active=False) -> Identifier:
        pass

    def insert(self, left_id, new_vertex):
        pass

    def insert_remote(self, left_id, new_vertex):
        return self.insert(left_id, new_vertex)

    def delete(self, id) -> Identifier:
        pass

    def get_initial_cursor(self):
        return None

    def get_repr(self, cursor):
        pass

    def get_detailed_repr(self):
        pass
