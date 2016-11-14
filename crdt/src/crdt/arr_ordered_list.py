from base_ordered_list import BaseOrderedList


class ArrOrderedList(BaseOrderedList):
    def __init__(self):
        self.nodes = {}
        self.olist = []

    def successor(self, vertex):
        super(ArrOrderedList, self).successor(vertex)

    def insert(self, vertex, new_vertex):
        super(ArrOrderedList, self).insert(vertex, new_vertex)

    def delete(self, vertex):
        super(ArrOrderedList, self).delete(vertex)

    def get_repr(self):
        super(ArrOrderedList, self).get_repr()

    def get_detailed_repr(self):
        super(ArrOrderedList, self).get_detailed_repr()
