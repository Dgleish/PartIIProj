class Node(object):
    def __init__(self, contents):
        self.contents = None
        self.atom = None
        self.clock = None

        # To identify the beginning and end of the list
        self.start_node = contents == 'START'
        self.end_node = contents == 'END'

        if not (self.start_node or self.end_node):
            self.contents = contents
            (self.atom, self.clock) = contents

        self.next_node = None
        self.prev_node = None
        # has this vertex been deleted?
        self.deleted = False

    def __str__(self):
        return '{}|{}'.format(self.atom, self.clock)

    def __repr__(self):
        return self.__str__()

class BaseOrderedList(object):
    def successor(self, clock, only_active=False):
        pass

    def predecessor(self, clock, only_active=False):
        pass

    def insert(self, left_clock, new_vertex):
        pass

    def delete(self, clock):
        pass

    def get_repr(self, cursor):
        pass

    def get_detailed_repr(self):
        pass
