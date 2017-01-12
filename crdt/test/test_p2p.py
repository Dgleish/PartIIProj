from time import sleep

from crdt.crdt_ops import CRDTOpAddRightLocal, CRDTOpDeleteLocal
from crdt_app import CRDTApp


def test_p2p(peer_list):
    print 'list of peers' + peer_list
    no_peers = len(peer_list)
    peers = [CRDTApp(chr(ord('A') + i), str(peer_list[i]), 8889, [
        CRDTOpAddRightLocal(chr(ord('a') + i)), CRDTOpDeleteLocal(), CRDTOpAddRightLocal(chr(ord('A') + i))
    ], peer_list[:i] + peer_list[i + 1:]) for i in xrange(no_peers)]
    sleep(20)
    s = set([p.crdt.pretty_print() for p in peers])
    print s
    assert len(s) == 1


import sys

if __name__ == '__main__':
    test_p2p(sys.argv[1:])
