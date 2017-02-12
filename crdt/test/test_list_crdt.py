import pytest

from crdt.crdt_clock import CRDTClock
from crdt.crdt_exceptions import VertexNotFound
from crdt.crdt_ops import CRDTOpAddRightLocal, CRDTOpAddRightRemote, CRDTOpDeleteRemote
from crdt.list_crdt import ListCRDT
from crdt.ll_ordered_list import LLOrderedList


@pytest.fixture(
    params=['A']
)
def list_crdt(request):
    return ListCRDT(request.param, LLOrderedList(request.param))


def test_mixture1(list_crdt):
    assert isinstance(list_crdt, ListCRDT)
    list_crdt.olist.insert(None, ('a', CRDTClock('A', 1)))
    list_crdt.olist.insert(None, ('b', CRDTClock('A', 2)))
    list_crdt.olist.insert(None, ('c', CRDTClock('A', 3)))
    list_crdt.olist.insert(None, ('d', CRDTClock('B', 1)))
    list_crdt.olist.insert(CRDTClock('A', 1), ('e', CRDTClock('A', 4)))
    list_crdt.delete_remote(CRDTOpDeleteRemote(CRDTClock('A', 2), None))
    list_crdt.delete_remote(CRDTOpDeleteRemote(CRDTClock('B', 1), None))
    res, cursor = list_crdt.pretty_print()
    assert res == 'cae'


def test_mixture2(list_crdt):
    assert isinstance(list_crdt, ListCRDT)
    list_crdt.olist.insert(None, ('a', CRDTClock('A', 1)))
    list_crdt.olist.insert(None, ('b', CRDTClock('A', 2)))
    list_crdt.olist.insert(None, ('c', CRDTClock('A', 3)))
    list_crdt.olist.insert(None, ('d', CRDTClock('B', 1)))
    list_crdt.olist.insert(CRDTClock('A', 1), ('e', CRDTClock('A', 4)))
    list_crdt.delete_remote(CRDTOpDeleteRemote(CRDTClock('A', 2), None))
    list_crdt.delete_remote(CRDTOpDeleteRemote(CRDTClock('A', 1), None))
    res, cursor = list_crdt.pretty_print()
    assert res == 'cde'


def test_remote_insert1(list_crdt):
    assert isinstance(list_crdt, ListCRDT)
    other_list_crdt = ListCRDT('C', LLOrderedList('C'))
    list_crdt.add_right_local(CRDTOpAddRightLocal('a'))
    other_list_crdt.add_right_remote(CRDTOpAddRightRemote(None, ('a', CRDTClock('A', 1)), CRDTClock('A', 1)))
    other_list_crdt.add_right_local(CRDTOpAddRightLocal('b'))
    list_crdt.add_right_local(CRDTOpAddRightLocal('c'))
    list_crdt.add_right_remote(CRDTOpAddRightRemote(None, ('b', CRDTClock('C', 2)), None))
    list_crdt.delete_remote(CRDTOpDeleteRemote(CRDTClock('C', 2), CRDTClock('C', 2)))
    other_list_crdt.add_right_remote(
        CRDTOpAddRightRemote(CRDTClock('A', 1), ('c', CRDTClock('A', 2)), CRDTClock('A', 2)))
    other_list_crdt.delete_remote(CRDTOpDeleteRemote(CRDTClock('C', 2), CRDTClock('C', 2)))
    assert list_crdt.pretty_print()[0] == other_list_crdt.pretty_print()[0]


def test_remote_insert2(list_crdt):
    assert isinstance(list_crdt, ListCRDT)
    other_list_crdt = ListCRDT('C', LLOrderedList('C'))
    list_crdt.add_right_local(CRDTOpAddRightLocal('a'))
    other_list_crdt.add_right_local(CRDTOpAddRightLocal('z'))
    other_list_crdt.add_right_remote(CRDTOpAddRightRemote(None, ('a', CRDTClock('A', 1)), None))
    other_list_crdt.add_right_local(CRDTOpAddRightLocal('b'))
    list_crdt.add_right_local(CRDTOpAddRightLocal('c'))
    list_crdt.add_right_remote(CRDTOpAddRightRemote(None, ('b', CRDTClock('C', 2)), None))
    list_crdt.delete_remote(CRDTOpDeleteRemote(CRDTClock('C', 2), None))
    other_list_crdt.add_right_remote(CRDTOpAddRightRemote(CRDTClock('A', 1), ('c', CRDTClock('A', 2)), None))
    other_list_crdt.delete_remote(CRDTOpDeleteRemote(CRDTClock('C', 2), None))
    list_crdt.add_right_remote(CRDTOpAddRightRemote(None, ('z', CRDTClock('C', 1)), None))
    assert list_crdt.pretty_print()[0] == other_list_crdt.pretty_print()[0]


def test_remote_insert3(list_crdt):
    assert isinstance(list_crdt, ListCRDT)
    list_crdt.add_right_remote(CRDTOpAddRightRemote(None, ('a', CRDTClock('A', 130)), CRDTClock('A', 130)))
    list_crdt.add_right_remote(CRDTOpAddRightRemote(None, ('b', CRDTClock('B', 130)), CRDTClock('B', 130)))
    list_crdt.add_right_remote(CRDTOpAddRightRemote(None, ('2', CRDTClock('A', 131)), CRDTClock('A', 131)))
    assert list_crdt.pretty_print()[0] == '2ba'


def test_add_local(list_crdt):
    assert isinstance(list_crdt, ListCRDT)
    list_crdt.add_right_local(CRDTOpAddRightLocal('a'))
    list_crdt.add_right_local(CRDTOpAddRightLocal('b'))
    list_crdt.add_right_local(CRDTOpAddRightLocal('c'))
    res = list_crdt.pretty_print()
    assert res[0] == 'abc'


def test_pretty_print(list_crdt):
    assert isinstance(list_crdt, ListCRDT)
    list_crdt.add_right_local(CRDTOpAddRightLocal('a'))
    list_crdt.add_right_local(CRDTOpAddRightLocal('b'))
    list_crdt.add_right_local(CRDTOpAddRightLocal('c'))
    res = list_crdt.pretty_print()
    assert res == ('abc', 3)


def test_pretty_print2(list_crdt):
    assert isinstance(list_crdt, ListCRDT)
    list_crdt.add_right_local(CRDTOpAddRightLocal('a'))
    list_crdt.add_right_local(CRDTOpAddRightLocal('b'))
    list_crdt.add_right_local(CRDTOpAddRightLocal('c'))
    list_crdt.delete_local()
    res = list_crdt.pretty_print()
    assert res == ('ab', 2)


def test_vertex_not_found(list_crdt):
    list_crdt.add_right_local(CRDTOpAddRightLocal('a'))
    with pytest.raises(VertexNotFound):
        list_crdt.add_right_remote(CRDTOpAddRightRemote(CRDTClock('A', 2), ('b', CRDTClock('A', 2)), None))
