import socket
from time import sleep

from crdt.crdt_ops import CRDTOpAddRightLocal
from crdt_app import CRDTApp
from crdt_network_server import CRDTServer

num_apps = 4
port = 12346


def test_crdt_app():
    ops = [
        [CRDTOpAddRightLocal(chr(ord('A') + i))]
        for i in xrange(num_apps)
        ]
    clients = [CRDTApp(chr(ord('A') + i), socket.gethostname(), port, ops[i], num_apps) for i in xrange(num_apps)]
    sleep(5)
    assert len(set([cl.crdt.pretty_print() for cl in clients])) == 1


def start_server():
    sv = CRDTServer(socket.gethostname(), port)
    print 'starting server'
    sv.listen()
