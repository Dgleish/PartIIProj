import sys

from crdt.crdt_ops import CRDTOpAddRightLocal, CRDTOpDeleteLocal
from crdt_app import CRDTApp


def run_p2p(my_addr, known_peers, encrypt=False, priv_key=None):
    app = CRDTApp(my_addr.replace('.', '')[-6:], 8889, [
        CRDTOpAddRightLocal(my_addr[0]), CRDTOpDeleteLocal(),
        CRDTOpAddRightLocal(my_addr[0])
    ], known_peers, my_addr, encrypt, priv_key)

if __name__ == '__main__':
    args = sys.argv
    print('got args {}'.format(args))
    if len(args) == 4:
        # without Tor
        run_p2p(
            args[1],
            [] if args[2] == ':' else args[2][1:-1].split(':'),
            encrypt=args[3] == '1'
        )
    else:
        # with Tor
        run_p2p(
            args[1],
            [] if args[2] == ':' else args[2][1:-1].split(':'),
            encrypt=args[3] == '1',
            priv_key=args[4]
        )
