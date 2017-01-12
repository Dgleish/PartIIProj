from crdt.crdt_ops import CRDTOpAddRightLocal, CRDTOpDeleteLocal
from crdt_app import CRDTApp


def run_p2p(puid, peer_list):
    no_peers = len(peer_list)
    app = CRDTApp(chr(ord('A') + int(puid[-1])), 'localhost', 8889, [
        CRDTOpAddRightLocal(chr(ord('a') + int(puid[-1]))), CRDTOpDeleteLocal(),
        CRDTOpAddRightLocal(chr(ord('A') + int(puid[-1])))
    ], peer_list)


import sys

if __name__ == '__main__':
    run_p2p(sys.argv[1], sys.argv[2:])
