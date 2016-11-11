import pytest

from crdt_exceptions import VertexNotFound
from list_crdt import ListCRDT
from ll_ordered_list import LLOrderedList

@pytest.fixture(
    params=['A']
)
def list_crdt(request):
    return ListCRDT(request.param,LLOrderedList())

def test_insert(list_crdt):
    assert isinstance(list_crdt,ListCRDT)
    list_crdt.add_right(None, ('a','1:A'))
    list_crdt.add_right(None, ('b','2:A'))
    list_crdt.add_right(None, ('c','3:A'))
    list_crdt.add_right(None, ('d','1:B'))
    list_crdt.add_right(('a','1:A'), ('e','4:A'))
    list_crdt.delete(('b','2:A'))
    list_crdt.delete(('d', '1:B'))
    res = list_crdt.pretty_print()
    assert res == 'cae'


def test_remote_insert(list_crdt):
    assert isinstance(list_crdt, ListCRDT)
    other_list_crdt = ListCRDT('C', LLOrderedList())
    list_crdt.add_right_local('a')

    other_list_crdt.add_right_remote(None, ('a', '1:A'))

    other_list_crdt.add_right_local('b')

    list_crdt.add_right_local('c')

    list_crdt.add_right_remote(None, ('b', '2:C'))
    list_crdt.delete(('b', '2:C'))

    other_list_crdt.add_right_remote(('a', '1:A'), ('c', '2:A'))
    other_list_crdt.delete(('b', '2:C'))
    assert list_crdt.pretty_print() == other_list_crdt.pretty_print()


def test_add_local(list_crdt):
    assert isinstance(list_crdt, ListCRDT)
    list_crdt.add_right_local('a')
    list_crdt.add_right_local('b')
    list_crdt.add_right_local('c')
    res = list_crdt.pretty_print()
    assert res == 'abc'


def test_vertex_not_found(list_crdt):
    list_crdt.add_right_local('a')
    with pytest.raises(VertexNotFound):
        list_crdt.add_right_remote(('b', '2:A'), ('b', '2:A'))
