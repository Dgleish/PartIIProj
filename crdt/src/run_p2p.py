import sys

from crdt.crdt_ops import CRDTOpAddRightLocal, CRDTOpDeleteLocal
from crdt_app import CRDTApp


def run_p2p(puid, known_peers, my_addr, priv_key=None):
    no_peers = len(known_peers)
    encrypt = False
    print('got args {} {} {} {}'.format(puid, known_peers, my_addr, priv_key))
    app = CRDTApp(chr(ord('A') + int(puid.split('.')[-1])), puid, 8889, [
        CRDTOpAddRightLocal(chr(ord('a') + int(puid.split('.')[-1]))), CRDTOpDeleteLocal(),
        CRDTOpAddRightLocal(chr(ord('A') + int(puid.split('.')[-1])))
    ], known_peers, my_addr, encrypt, priv_key)


if __name__ == '__main__':
    args = sys.argv
    if len(args) == 3:
        # without Tor
        run_p2p(args[1], args[2][:-1].split(':'), args[1])
    else:
        run_p2p(args[1], args[3][:-1].split(':'), args[2], args[4])
