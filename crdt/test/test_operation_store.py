import pytest

from crdt.crdt_clock import CRDTClock
from crdt.crdt_ops import CRDTOpDeleteRemote
from tools.operation_store import OperationStore


@pytest.fixture(params=[list, set])
def op_store(request) -> OperationStore:
    return OperationStore(request.param)


def test_add_op_list():
    op_store = OperationStore(list)
    op_store.add_op('key', 'val')
    op_store.add_op('key', 'val')
    assert list(op_store.ops['key']) == ['val', 'val']


def test_add_op_set():
    op_store = OperationStore(set)
    op_store.add_op('key', 'val')
    op_store.add_op('key', 'val')
    assert list(op_store.ops['key']) == ['val']


def test_remove_ops_for_key(op_store: OperationStore):
    op_store.add_op('key', 'val')
    op_store.add_op('key', 'val')
    op_store.remove_ops_for_key('key')
    assert len(op_store.get_ops_for_key('key')) == 0


def test_get_ops_for_key(op_store: OperationStore):
    to_add = [('key1', 'val1'), ('key2', 'val2')]
    for k, v in to_add:
        op_store.add_op(k, v)
    assert len(op_store.get_ops_for_key('key1')) == 1 and (
        len(op_store.get_ops_for_key('key2')) == 1)


def test_get_ops_after1():
    op_store = OperationStore(list)
    ops = [CRDTOpDeleteRemote(None, CRDTClock('A', 5)), CRDTOpDeleteRemote(None, CRDTClock('A', 6))]
    op_store.ops['A'] = ops
    result = op_store._get_ops_for_key_after('A', None)
    assert len(result) == len(ops)


def test_get_ops_after2():
    op_store = OperationStore(list)
    ops = [CRDTOpDeleteRemote(None, CRDTClock('A', 5)), CRDTOpDeleteRemote(None, CRDTClock('A', 6))]
    op_store.ops['A'] = ops
    result = op_store._get_ops_for_key_after('A', CRDTClock('A', 5))
    assert len(result) == len(ops) - 1


def test_get_ops_after3():
    op_store = OperationStore(list)
    ops = [
        CRDTOpDeleteRemote(None, CRDTClock('A', 0)),
        CRDTOpDeleteRemote(None, CRDTClock('A', 5)),
        CRDTOpDeleteRemote(None, CRDTClock('A', 6)),
        CRDTOpDeleteRemote(None, CRDTClock('A', 9000))
    ]
    op_store.ops['A'] = ops
    result = op_store._get_ops_for_key_after('A', CRDTClock('A', 5))
    assert len(result) == 2


def test_get_ops_after4():
    op_store = OperationStore(list)
    ops = {
        'A': [
            CRDTOpDeleteRemote(None, CRDTClock('A', 2)),
            CRDTOpDeleteRemote(None, CRDTClock('A', 5)),
            CRDTOpDeleteRemote(None, CRDTClock('A', 6)),
            CRDTOpDeleteRemote(None, CRDTClock('A', 9))
        ],
        'B': [
            CRDTOpDeleteRemote(None, CRDTClock('B', 2)),
            CRDTOpDeleteRemote(None, CRDTClock('B', 5)),
            CRDTOpDeleteRemote(None, CRDTClock('B', 6)),
            CRDTOpDeleteRemote(None, CRDTClock('B', 9))
        ]
    }
    op_store.ops = ops
    result = op_store._get_ops_for_key_after('B', CRDTClock('B', 5))
    assert len(result) == 2


def test_get_ops_after5():
    op_store = OperationStore(list)
    ops = [
        CRDTOpDeleteRemote(None, CRDTClock('A', 0)),
        CRDTOpDeleteRemote(None, CRDTClock('A', 1)),
        CRDTOpDeleteRemote(None, CRDTClock('A', 6)),
        CRDTOpDeleteRemote(None, CRDTClock('A', 9))
    ]
    op_store.ops['A'] = ops
    result = op_store._get_ops_for_key_after('A', CRDTClock('A', 0))
    assert len(result) == 3


def test_determine_ops():
    pass
