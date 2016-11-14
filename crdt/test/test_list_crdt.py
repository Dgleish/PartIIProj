import pytest

from crdt.crdt_exceptions import VertexNotFound
from crdt.crdt_ops import CRDTOpAddRightLocal, CRDTOpAddRightRemote, CRDTOpDeleteRemote
from crdt.list_crdt import ListCRDT
from crdt.ll_ordered_list import LLOrderedList


@pytest.fixture(
    params=['A']
)
def list_crdt(request):
    return ListCRDT(request.param,LLOrderedList())


def test_mixture(list_crdt):
    assert isinstance(list_crdt,ListCRDT)
    list_crdt._add_right(None, ('a', '1:A'))
    list_crdt._add_right(None, ('b', '2:A'))
    list_crdt._add_right(None, ('c', '3:A'))
    list_crdt._add_right(None, ('d', '1:B'))
    list_crdt._add_right('1:A', ('e', '4:A'))
    list_crdt.delete_remote(CRDTOpDeleteRemote('2:A'))
    list_crdt.delete_remote(CRDTOpDeleteRemote('1:B'))
    res = list_crdt.pretty_print()
    assert res == 'cae'


def test_remote_insert(list_crdt):
    assert isinstance(list_crdt, ListCRDT)
    other_list_crdt = ListCRDT('C', LLOrderedList())
    list_crdt.add_right_local(CRDTOpAddRightLocal('a'))
    other_list_crdt.add_right_remote(CRDTOpAddRightRemote(None, ('a', '1:A')))
    other_list_crdt.add_right_local(CRDTOpAddRightLocal('b'))
    list_crdt.add_right_local(CRDTOpAddRightLocal('c'))
    list_crdt.add_right_remote(CRDTOpAddRightRemote(None, ('b', '2:C')))
    list_crdt.delete_remote(CRDTOpDeleteRemote('2:C'))
    other_list_crdt.add_right_remote(CRDTOpAddRightRemote('1:A', ('c', '2:A')))
    other_list_crdt.delete_remote(CRDTOpDeleteRemote('2:C'))
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
        list_crdt.add_right_remote(CRDTOpAddRightRemote('2:A', ('b', '2:A')))
