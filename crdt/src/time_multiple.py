import sys

from crdt.crdt_ops import CRDTOpAddRightLocal
from crdt_app import CRDTApp


def run_p2p(my_addr, known_peers, encrypt=False, priv_key=None):
    for i in range(100):
        print('Iteration {}'.format(i + 1))
        app = CRDTApp(my_addr.replace('.', '')[-6:], 8889, my_addr,
                      ops_to_do=[CRDTOpAddRightLocal(my_addr[-1])] * 1000,
                      # ops_to_do=[],
                      known_peers=known_peers, encrypt=encrypt, priv_key=priv_key)


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
