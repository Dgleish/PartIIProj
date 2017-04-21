import pytest

from crdt.clock_id import ClockID
from crdt.ops import CRDTOpDeleteRemote
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
    ops = [CRDTOpDeleteRemote(None, ClockID('A', 5)), CRDTOpDeleteRemote(None, ClockID('A', 6))]
    op_store.ops['A'] = ops
    result = op_store._get_ops_for_key_after('A', None)
    assert len(result) == len(ops)


def test_get_ops_after2():
    op_store = OperationStore(list)
    ops = [CRDTOpDeleteRemote(None, ClockID('A', 5)), CRDTOpDeleteRemote(None, ClockID('A', 6))]
    op_store.ops['A'] = ops
    result = op_store._get_ops_for_key_after('A', ClockID('A', 5))
    assert len(result) == len(ops) - 1


def test_get_ops_after3():
    op_store = OperationStore(list)
    ops = [
        CRDTOpDeleteRemote(None, ClockID('A', 0)),
        CRDTOpDeleteRemote(None, ClockID('A', 5)),
        CRDTOpDeleteRemote(None, ClockID('A', 6)),
        CRDTOpDeleteRemote(None, ClockID('A', 9000))
    ]
    op_store.ops['A'] = ops
    result = op_store._get_ops_for_key_after('A', ClockID('A', 5))
    assert len(result) == 2


def test_get_ops_after4():
    op_store = OperationStore(list)
    ops = {
        'A': [
            CRDTOpDeleteRemote(None, ClockID('A', 2)),
            CRDTOpDeleteRemote(None, ClockID('A', 5)),
            CRDTOpDeleteRemote(None, ClockID('A', 6)),
            CRDTOpDeleteRemote(None, ClockID('A', 9))
        ],
        'B': [
            CRDTOpDeleteRemote(None, ClockID('B', 2)),
            CRDTOpDeleteRemote(None, ClockID('B', 5)),
            CRDTOpDeleteRemote(None, ClockID('B', 6)),
            CRDTOpDeleteRemote(None, ClockID('B', 9))
        ]
    }
    op_store.ops = ops
    result = op_store._get_ops_for_key_after('B', ClockID('B', 5))
    assert len(result) == 2


def test_get_ops_after5():
    op_store = OperationStore(list)
    ops = [
        CRDTOpDeleteRemote(None, ClockID('A', 0)),
        CRDTOpDeleteRemote(None, ClockID('A', 1)),
        CRDTOpDeleteRemote(None, ClockID('A', 6)),
        CRDTOpDeleteRemote(None, ClockID('A', 9))
    ]
    op_store.ops['A'] = ops
    result = op_store._get_ops_for_key_after('A', ClockID('A', 0))
    assert len(result) == 3


def test_undo1():
    op_store = OperationStore(list)
    ops = [
        CRDTOpDeleteRemote(None, ClockID('A', 1)),
        CRDTOpDeleteRemote(None, ClockID('A', 3))
    ]
    for op in ops:
        op_store.add_op('A', op)
    undo_op = op_store.undo('A')
    op_store.add_op('A', undo_op, True)
    assert undo_op == ops[1] == op_store.undone_ops[0]


def test_undo2():
    op_store = OperationStore(list)
    ops = [
        CRDTOpDeleteRemote(None, ClockID('A', 1)),
        CRDTOpDeleteRemote(None, ClockID('A', 3)),
        CRDTOpDeleteRemote(None, ClockID('A', 4)),
        CRDTOpDeleteRemote(None, ClockID('A', 5)),
        CRDTOpDeleteRemote(None, ClockID('A', 6)),
        CRDTOpDeleteRemote(None, ClockID('A', 7)),
    ]
    for op in ops:
        op_store.add_op('A', op)
    undo_op = None

    for _ in range(3):
        undo_op = op_store.undo('A')
        op_store.add_op('A', undo_op, True)

    redo_op = op_store.redo('A')
    op_store.add_op('A', redo_op)

    for _ in range(3):
        undo_op = op_store.undo('A')
        op_store.add_op('A', undo_op, True)

    assert undo_op == ops[1] == op_store.undone_ops[-1]


def test_undo3():
    op_store = OperationStore(list)
    ops = [
        CRDTOpDeleteRemote(None, ClockID('A', 1)),
        CRDTOpDeleteRemote(None, ClockID('A', 3))
    ]
    for op in ops:
        op_store.add_op('A', op)

    undo_op = op_store.undo('A')
    op_store.add_op('A', undo_op, True)

    redo_op = op_store.redo('A')
    op_store.add_op('A', redo_op)
    assert op_store.ops['A'][-1] == undo_op

def test_determine_ops():
    pass
