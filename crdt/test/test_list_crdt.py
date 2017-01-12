import logging

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
    return ListCRDT(request.param, LLOrderedList())


def test_mixture1(list_crdt):
    assert isinstance(list_crdt, ListCRDT)
    list_crdt._add_right(None, ('a', CRDTClock('A', 1)))
    list_crdt._add_right(None, ('b', CRDTClock('A', 2)))
    list_crdt._add_right(None, ('c', CRDTClock('A', 3)))
    list_crdt._add_right(None, ('d', CRDTClock('B', 1)))
    list_crdt._add_right(CRDTClock('A', 1), ('e', CRDTClock('A', 4)))
    list_crdt.delete_remote(CRDTOpDeleteRemote(CRDTClock('A', 2)))
    list_crdt.delete_remote(CRDTOpDeleteRemote(CRDTClock('B', 1)))
    res = list_crdt.pretty_print()
    logging.debug(res)
    assert res == 'cae'


def test_mixture2(list_crdt):
    assert isinstance(list_crdt, ListCRDT)
    list_crdt._add_right(None, ('a', CRDTClock('A', 1)))
    list_crdt._add_right(None, ('b', CRDTClock('A', 2)))
    list_crdt._add_right(None, ('c', CRDTClock('A', 3)))
    list_crdt._add_right(None, ('d', CRDTClock('B', 1)))
    list_crdt._add_right(CRDTClock('A', 1), ('e', CRDTClock('A', 4)))
    list_crdt.delete_remote(CRDTOpDeleteRemote(CRDTClock('A', 2)))
    list_crdt.delete_remote(CRDTOpDeleteRemote(CRDTClock('A', 1)))
    res = list_crdt.pretty_print()
    logging.debug(res)
    assert res == 'cde'


def test_remote_insert1(list_crdt):
    assert isinstance(list_crdt, ListCRDT)
    other_list_crdt = ListCRDT('C', LLOrderedList())
    list_crdt.add_right_local(CRDTOpAddRightLocal('a'))
    other_list_crdt.add_right_remote(CRDTOpAddRightRemote(None, ('a', CRDTClock('A', 1))))
    other_list_crdt.add_right_local(CRDTOpAddRightLocal('b'))
    list_crdt.add_right_local(CRDTOpAddRightLocal('c'))
    list_crdt.add_right_remote(CRDTOpAddRightRemote(None, ('b', CRDTClock('C', 2))))
    list_crdt.delete_remote(CRDTOpDeleteRemote(CRDTClock('C', 2)))
    other_list_crdt.add_right_remote(CRDTOpAddRightRemote(CRDTClock('A', 1), ('c', CRDTClock('A', 2))))
    other_list_crdt.delete_remote(CRDTOpDeleteRemote(CRDTClock('C', 2)))
    logging.debug(list_crdt.pretty_print())
    assert list_crdt.pretty_print() == other_list_crdt.pretty_print()


def test_remote_insert2(list_crdt):
    assert isinstance(list_crdt, ListCRDT)
    other_list_crdt = ListCRDT('C', LLOrderedList())
    list_crdt.add_right_local(CRDTOpAddRightLocal('a'))
    other_list_crdt.add_right_local(CRDTOpAddRightLocal('z'))
    other_list_crdt.add_right_remote(CRDTOpAddRightRemote(None, ('a', CRDTClock('A', 1))))
    other_list_crdt.add_right_local(CRDTOpAddRightLocal('b'))
    list_crdt.add_right_local(CRDTOpAddRightLocal('c'))
    list_crdt.add_right_remote(CRDTOpAddRightRemote(None, ('b', CRDTClock('C', 2))))
    list_crdt.delete_remote(CRDTOpDeleteRemote(CRDTClock('C', 2)))
    other_list_crdt.add_right_remote(CRDTOpAddRightRemote(CRDTClock('A', 1), ('c', CRDTClock('A', 2))))
    other_list_crdt.delete_remote(CRDTOpDeleteRemote(CRDTClock('C', 2)))
    list_crdt.add_right_remote(CRDTOpAddRightRemote(None, ('z', CRDTClock('C', 1))))
    logging.debug(list_crdt.pretty_print())
    assert list_crdt.pretty_print() == other_list_crdt.pretty_print()


def test_add_local(list_crdt):
    assert isinstance(list_crdt, ListCRDT)
    list_crdt.add_right_local(CRDTOpAddRightLocal('a'))
    list_crdt.add_right_local(CRDTOpAddRightLocal('b'))
    list_crdt.add_right_local(CRDTOpAddRightLocal('c'))
    res = list_crdt.pretty_print()
    assert res == 'abc'


def test_vertex_not_found(list_crdt):
    list_crdt.add_right_local(CRDTOpAddRightLocal('a'))
    with pytest.raises(VertexNotFound):
        list_crdt.add_right_remote(CRDTOpAddRightRemote(CRDTClock('A', 2), ('b', CRDTClock('A', 2))))
