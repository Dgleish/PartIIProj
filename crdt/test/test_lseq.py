import pytest

from crdt.list_crdt import ListCRDT
from crdt.ops import OpAddRightLocal, OpDeleteLocal
from crdt.ordered_list.lseq_ordered_list import LSEQOrderedList

puid = 'a'


@pytest.fixture()
def lseq(request):
    return ListCRDT(puid, LSEQOrderedList(puid))


def test_insert1(lseq):
    assert isinstance(lseq, ListCRDT)
    lseq.perform_op(OpAddRightLocal('a'))
    lseq.perform_op(OpAddRightLocal('b'))
    lseq.perform_op(OpAddRightLocal('c'))
    assert lseq.pretty_print()[0] == 'abc'


def test_insert2(lseq):
    assert isinstance(lseq, ListCRDT)
    lseq.perform_op(OpAddRightLocal('a'))
    lseq.shift_cursor_left()
    lseq.perform_op(OpAddRightLocal('b'))
    lseq.shift_cursor_left()
    lseq.perform_op(OpAddRightLocal('c'))
    assert lseq.pretty_print()[0] == 'cba'


def test_insert3(lseq):
    assert isinstance(lseq, ListCRDT)
    lseq.perform_op(OpAddRightLocal('1'))
    lseq.perform_op(OpAddRightLocal('%'))
    lseq.perform_op(OpAddRightLocal('$'))
    assert lseq.pretty_print()[0] == '1%$'


def test_delete1(lseq):
    assert isinstance(lseq, ListCRDT)
    lseq.perform_op(OpAddRightLocal('a'))
    lseq.perform_op(OpAddRightLocal('b'))
    lseq.perform_op(OpAddRightLocal('c'))
    lseq.perform_op(OpDeleteLocal())
    lseq.shift_cursor_left()
    lseq.perform_op(OpDeleteLocal())
    assert lseq.pretty_print()[0] == 'b'


def test_delete2(lseq):
    assert isinstance(lseq, ListCRDT)
    lseq.perform_op(OpAddRightLocal('a'))
    lseq.perform_op(OpAddRightLocal('b'))
    lseq.perform_op(OpAddRightLocal('c'))
    lseq.perform_op(OpDeleteLocal())
    lseq.perform_op(OpDeleteLocal())
    lseq.perform_op(OpDeleteLocal())
    assert lseq.pretty_print()[0] == ''


def test_delete3(lseq):
    assert isinstance(lseq, ListCRDT)
    lseq.perform_op(OpDeleteLocal())
    lseq.perform_op(OpDeleteLocal())
    lseq.perform_op(OpDeleteLocal())
    lseq.perform_op(OpDeleteLocal())
    assert lseq.pretty_print()[0] == ''


def test_delete4(lseq):
    assert isinstance(lseq, ListCRDT)
    lseq.perform_op(OpDeleteLocal())
    lseq.perform_op(OpDeleteLocal())
    lseq.perform_op(OpDeleteLocal())
    lseq.perform_op(OpDeleteLocal())
    assert lseq.pretty_print()[0] == ''
