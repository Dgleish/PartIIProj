import socket
from time import sleep

from crdt.crdt_ops import CRDTOpAddRightLocal, CRDTOpDeleteLocal
from crdt_app import CRDTApp

num_apps = 12
port = 12346


def test_crdt_app():
    ops = [
        [CRDTOpAddRightLocal(chr(ord('a') + i)), CRDTOpDeleteLocal(), CRDTOpAddRightLocal(chr(ord('A') + i))]
        for i in xrange(num_apps)
        ]
    clients = [CRDTApp(chr(ord('A') + i), socket.gethostname(), port, ops[i]) for i in xrange(num_apps)]
    sleep(20)
    s = set([cl.crdt.pretty_print() for cl in clients])
    print s
    assert len(s) == 1


# def test_crdt_app2():
#     ops = [
#         [CRDTOpAddRightLocal(chr(ord('a') + i)), CRDTOpDeleteLocal(), CRDTOpAddRightLocal(chr(ord('A') + i))]
#         for i in xrange(num_apps)
#         ]
#     clients = [CRDTApp(chr(ord('A') + i), socket.gethostname(), port, ops[i], num_apps) for i in xrange(num_apps)]
#     sleep(10)
#     assert len(set([cl.crdt.pretty_print() for cl in clients])) == 1


# def start_server():
#     sv = CRDTServer(socket.gethostname(), port)
#     print 'starting server'
#     sv.listen()
