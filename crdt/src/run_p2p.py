import sys

from crdt.crdt_ops import CRDTOpAddRightLocal, CRDTOpDeleteLocal
from crdt_app import CRDTApp


def run_p2p(puid, known_peers, my_addr, encrypt=False, priv_key=None):
    no_peers = len(known_peers)
    app = CRDTApp(chr(ord('A') + int(puid.split('.')[-1])), puid, 8889, [
        CRDTOpAddRightLocal(chr(ord('a') + int(puid.split('.')[-1]))), CRDTOpDeleteLocal(),
        CRDTOpAddRightLocal(chr(ord('A') + int(puid.split('.')[-1])))
    ], known_peers, my_addr, encrypt, priv_key)


if __name__ == '__main__':
    args = sys.argv
    print('got args {}'.format(args))
    if len(args) == 3:
        run_p2p(args[1], [], args[1], encrypt=args[2] == '1')
    elif len(args) == 4:
        # without Tor
        run_p2p(args[1], args[2][:-1].split(':'), args[1], encrypt=args[3] == '1')
    elif len(args) == 5:
        run_p2p(args[1], [], args[2], encrypt=args[4] == '1', priv_key=args[3])
    else:
        run_p2p(args[1], args[3][:-1].split(':'), args[2], encrypt=args[5] == '1', priv_key=args[4])
