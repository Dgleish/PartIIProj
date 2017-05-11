import pytest

from crdt.clock_id import ClockID
from crdt.crdt_exceptions import VertexNotFound
from crdt.list_crdt import ListCRDT
from crdt.ops import OpAddRightLocal, OpAddRightRemote, CRDTOpDeleteRemote
from crdt.ordered_list.arr_ordered_list import ArrOrderedList
from crdt.ordered_list.ll_ordered_list import LLOrderedList


@pytest.fixture(
    params=[LLOrderedList, ArrOrderedList]
)
def list_crdt(request):
    return ListCRDT('A', request.param('A'))


def test_mixture1(list_crdt):
    assert isinstance(list_crdt, ListCRDT)
    list_crdt.olist.insert(None, ('a', ClockID('A', 1)))
    list_crdt.olist.insert(None, ('b', ClockID('A', 2)))
    list_crdt.olist.insert(None, ('c', ClockID('A', 3)))
    list_crdt.olist.insert(None, ('d', ClockID('B', 1)))
    list_crdt.olist.insert(ClockID('A', 1), ('e', ClockID('A', 4)))
    list_crdt.delete_remote(CRDTOpDeleteRemote(('b', ClockID('A', 2)), None))
    list_crdt.delete_remote(CRDTOpDeleteRemote(('d', ClockID('B', 1)), None))
    res, cursor = list_crdt.pretty_print()
    assert res == 'cae'


def test_mixture2(list_crdt):
    assert isinstance(list_crdt, ListCRDT)
    list_crdt.olist.insert(None, ('a', ClockID('A', 1)))
    list_crdt.olist.insert(None, ('b', ClockID('A', 2)))
    list_crdt.olist.insert(None, ('c', ClockID('A', 3)))
    list_crdt.olist.insert(None, ('d', ClockID('B', 1)))
    list_crdt.olist.insert(ClockID('A', 1), ('e', ClockID('A', 4)))
    list_crdt.delete_remote(CRDTOpDeleteRemote(('b', ClockID('A', 2)), None))
    list_crdt.delete_remote(CRDTOpDeleteRemote(('a', ClockID('A', 1)), None))
    res, cursor = list_crdt.pretty_print()
    assert res == 'cde'


def test_mixture3(list_crdt):
    assert isinstance(list_crdt, ListCRDT)
    list_crdt.olist.insert(None, ('a', ClockID('A', 1)))
    list_crdt.olist.insert(ClockID('A', 1), ('e', ClockID('A', 2)))
    res, cursor = list_crdt.pretty_print()
    assert res == 'ae'


def test_remote_insert1(list_crdt):
    assert isinstance(list_crdt, ListCRDT)
    other_list_crdt = ListCRDT('C', LLOrderedList('C'))
    list_crdt.add_right_local(OpAddRightLocal('a'))
    other_list_crdt.add_right_remote(OpAddRightRemote(None, ('a', ClockID('A', 1)), ClockID('A', 1)))
    other_list_crdt.add_right_local(OpAddRightLocal('b'))
    list_crdt.add_right_local(OpAddRightLocal('c'))
    list_crdt.add_right_remote(OpAddRightRemote(None, ('b', ClockID('C', 2)), None))
    list_crdt.delete_remote(CRDTOpDeleteRemote(('b', ClockID('C', 2)), ClockID('C', 2)))
    other_list_crdt.add_right_remote(
        OpAddRightRemote(ClockID('A', 1), ('c', ClockID('A', 2)), ClockID('A', 2)))
    other_list_crdt.delete_remote(CRDTOpDeleteRemote(('b', ClockID('C', 2)), ClockID('C', 2)))
    assert list_crdt.pretty_print()[0] == other_list_crdt.pretty_print()[0]


def test_remote_insert2(list_crdt):
    assert isinstance(list_crdt, ListCRDT)
    other_list_crdt = ListCRDT('C', LLOrderedList('C'))
    list_crdt.add_right_local(OpAddRightLocal('a'))
    other_list_crdt.add_right_local(OpAddRightLocal('z'))
    other_list_crdt.add_right_remote(OpAddRightRemote(None, ('a', ClockID('A', 1)), None))
    other_list_crdt.add_right_local(OpAddRightLocal('b'))
    list_crdt.add_right_local(OpAddRightLocal('c'))
    list_crdt.add_right_remote(OpAddRightRemote(None, ('b', ClockID('C', 2)), None))
    list_crdt.delete_remote(CRDTOpDeleteRemote(('b', ClockID('C', 2)), None))
    other_list_crdt.add_right_remote(OpAddRightRemote(ClockID('A', 1), ('c', ClockID('A', 2)), None))
    other_list_crdt.delete_remote(CRDTOpDeleteRemote(('b', ClockID('C', 2)), None))
    list_crdt.add_right_remote(OpAddRightRemote(None, ('z', ClockID('C', 1)), None))
    assert list_crdt.pretty_print()[0] == other_list_crdt.pretty_print()[0]


def test_remote_insert3(list_crdt):
    assert isinstance(list_crdt, ListCRDT)
    list_crdt.add_right_remote(OpAddRightRemote(None, ('a', ClockID('A', 130)), ClockID('A', 130)))
    list_crdt.add_right_remote(OpAddRightRemote(None, ('b', ClockID('B', 130)), ClockID('B', 130)))
    list_crdt.add_right_remote(OpAddRightRemote(None, ('2', ClockID('A', 131)), ClockID('A', 131)))
    assert list_crdt.pretty_print()[0] == '2ba'


def test_add_local(list_crdt):
    assert isinstance(list_crdt, ListCRDT)
    list_crdt.add_right_local(OpAddRightLocal('a'))
    list_crdt.add_right_local(OpAddRightLocal('b'))
    list_crdt.add_right_local(OpAddRightLocal('c'))
    res = list_crdt.pretty_print()
    assert res[0] == 'abc'


def test_pretty_print(list_crdt):
    assert isinstance(list_crdt, ListCRDT)
    list_crdt.add_right_local(OpAddRightLocal('a'))
    list_crdt.add_right_local(OpAddRightLocal('b'))
    list_crdt.add_right_local(OpAddRightLocal('c'))
    res = list_crdt.pretty_print()
    assert res == ('abc', 3)


def test_pretty_print2(list_crdt):
    assert isinstance(list_crdt, ListCRDT)
    list_crdt.add_right_local(OpAddRightLocal('a'))
    list_crdt.add_right_local(OpAddRightLocal('b'))
    list_crdt.add_right_local(OpAddRightLocal('c'))
    list_crdt.delete_local()
    res = list_crdt.pretty_print()
    assert res == ('ab', 2)


def test_vertex_not_found(list_crdt):
    list_crdt.add_right_local(OpAddRightLocal('a'))
    with pytest.raises(VertexNotFound):
        list_crdt.add_right_remote(OpAddRightRemote(ClockID('A', 2), ('b', ClockID('A', 2)), None))
