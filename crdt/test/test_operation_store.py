from crdt.crdt_clock import CRDTClock
from crdt.crdt_ops import CRDTOpDeleteRemote
from tools.operation_store import OperationStore


def test_get_ops_after1():
    op_store = OperationStore()
    ops = [CRDTOpDeleteRemote(None, CRDTClock('A', 5)), CRDTOpDeleteRemote(None, CRDTClock('A', 6))]
    op_store.ops['A'] = ops
    result = op_store.get_ops_after('A', None)
    assert len(result) == len(ops)


def test_get_ops_after2():
    op_store = OperationStore()
    ops = [CRDTOpDeleteRemote(None, CRDTClock('A', 5)), CRDTOpDeleteRemote(None, CRDTClock('A', 6))]
    op_store.ops['A'] = ops
    result = op_store.get_ops_after('A', CRDTClock('A', 5))
    assert len(result) == len(ops) - 1


def test_get_ops_after3():
    op_store = OperationStore()
    ops = [
        CRDTOpDeleteRemote(None, CRDTClock('A', 0)),
        CRDTOpDeleteRemote(None, CRDTClock('A', 5)),
        CRDTOpDeleteRemote(None, CRDTClock('A', 6)),
        CRDTOpDeleteRemote(None, CRDTClock('A', 9000))
    ]
    op_store.ops['A'] = ops
    result = op_store.get_ops_after('A', CRDTClock('A', 5))
    assert len(result) == 2


def test_get_ops_after4():
    op_store = OperationStore()
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
    result = op_store.get_ops_after('B', CRDTClock('B', 5))
    assert len(result) == 2


def test_get_ops_after5():
    op_store = OperationStore()
    ops = [
        CRDTOpDeleteRemote(None, CRDTClock('A', 0)),
        CRDTOpDeleteRemote(None, CRDTClock('A', 1)),
        CRDTOpDeleteRemote(None, CRDTClock('A', 6)),
        CRDTOpDeleteRemote(None, CRDTClock('A', 9))
    ]
    op_store.ops['A'] = ops
    result = op_store.get_ops_after('A', CRDTClock('A', 0))
    assert len(result) == 3


def test_determine_ops():
    pass
