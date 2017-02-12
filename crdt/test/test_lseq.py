import pytest

from crdt.crdt_ops import CRDTOpAddRightLocal, CRDTOpDeleteLocal
from crdt.list_crdt import ListCRDT
from crdt.lseq_ordered_list import LSEQOrderedList

puid = 'a'


@pytest.fixture()
def lseq(request):
    return ListCRDT(puid, LSEQOrderedList(puid))


def test_insert1(lseq):
    assert isinstance(lseq, ListCRDT)
    lseq.perform_op(CRDTOpAddRightLocal('a'))
    lseq.perform_op(CRDTOpAddRightLocal('b'))
    lseq.perform_op(CRDTOpAddRightLocal('c'))
    assert lseq.pretty_print()[0] == 'abc'


def test_insert2(lseq):
    assert isinstance(lseq, ListCRDT)
    lseq.perform_op(CRDTOpAddRightLocal('a'))
    lseq.shift_cursor_left()
    lseq.perform_op(CRDTOpAddRightLocal('b'))
    lseq.shift_cursor_left()
    lseq.perform_op(CRDTOpAddRightLocal('c'))
    assert lseq.pretty_print()[0] == 'cba'


def test_insert3(lseq):
    assert isinstance(lseq, ListCRDT)
    lseq.perform_op(CRDTOpAddRightLocal('1'))
    lseq.perform_op(CRDTOpAddRightLocal('%'))
    lseq.perform_op(CRDTOpAddRightLocal('$'))
    assert lseq.pretty_print()[0] == '1%$'


def test_delete1(lseq):
    assert isinstance(lseq, ListCRDT)
    lseq.perform_op(CRDTOpAddRightLocal('a'))
    lseq.perform_op(CRDTOpAddRightLocal('b'))
    lseq.perform_op(CRDTOpAddRightLocal('c'))
    lseq.perform_op(CRDTOpDeleteLocal())
    lseq.shift_cursor_left()
    lseq.perform_op(CRDTOpDeleteLocal())
    assert lseq.pretty_print()[0] == 'b'


def test_delete2(lseq):
    assert isinstance(lseq, ListCRDT)
    lseq.perform_op(CRDTOpAddRightLocal('a'))
    lseq.perform_op(CRDTOpAddRightLocal('b'))
    lseq.perform_op(CRDTOpAddRightLocal('c'))
    lseq.perform_op(CRDTOpDeleteLocal())
    lseq.perform_op(CRDTOpDeleteLocal())
    lseq.perform_op(CRDTOpDeleteLocal())
    assert lseq.pretty_print()[0] == ''


def test_delete3(lseq):
    assert isinstance(lseq, ListCRDT)
    lseq.perform_op(CRDTOpDeleteLocal())
    lseq.perform_op(CRDTOpDeleteLocal())
    lseq.perform_op(CRDTOpDeleteLocal())
    lseq.perform_op(CRDTOpDeleteLocal())
    assert lseq.pretty_print()[0] == ''


def test_delete4(lseq):
    assert isinstance(lseq, ListCRDT)
    lseq.perform_op(CRDTOpDeleteLocal())
    lseq.perform_op(CRDTOpDeleteLocal())
    lseq.perform_op(CRDTOpDeleteLocal())
    lseq.perform_op(CRDTOpDeleteLocal())
    assert lseq.pretty_print()[0] == ''
