from crdt.ops import CRDTOpDeleteRemote, OpDeleteLocal
from tools.operation_queue import OperationQueue


def test_queue1():
    q = OperationQueue()
    q.append(CRDTOpDeleteRemote(None, None))
    q.append(CRDTOpDeleteRemote(None, None))
    assert len(q.queue) == 2


def test_queue2():
    q = OperationQueue()
    ops = [CRDTOpDeleteRemote(None, None)] * 200
    for o in ops:
        q.append(o)
    ops = []
    while len(q.queue) > 0:
        ops.append(q.popleft())
    assert len(ops) == 200


def test_queue3():
    q = OperationQueue()
    ops = [CRDTOpDeleteRemote(None, None), OpDeleteLocal()]
    for o in ops:
        q.append(o)
    ops = []

    while len(q.queue) > 0:
        ops.append(q.popleft())
    assert isinstance(ops[0], CRDTOpDeleteRemote) and isinstance(ops[1], OpDeleteLocal)
