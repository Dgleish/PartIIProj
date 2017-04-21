import sys

from crdt.ops import OpAddRightLocal
from crdt_app import CRDTApp


def run_p2p(my_addr, known_peers, encrypt=False, priv_key=None, my_cookie=None, other_cookies=None):
    auth_cookies = None
    if other_cookies is not None:
        auth_cookies = dict(zip(known_peers, other_cookies))
    app = CRDTApp(my_addr.replace('.', '')[-6:], 8889, my_addr,
                  ops_to_do=[OpAddRightLocal(my_addr[-1])] * 1, known_peers=known_peers,
                  encrypt=encrypt, priv_key=priv_key, auth_cookies=auth_cookies, my_cookie=my_cookie)


if __name__ == '__main__':
    args = sys.argv
    print('got args {}'.format(args))
    if len(args) == 4:
        # without Tor
        run_p2p(
            args[1],
            [] if args[2] == ':' else args[2].split(':')[1:-1],
            encrypt=args[3] == '1'
        )
    elif len(args) == 5:
        # with Tor
        run_p2p(
            args[1],
            [] if args[2] == ':' else args[2].split(':')[1:-1],
            encrypt=args[3] == '1',
            priv_key=args[4]
        )
    else:
        # with Tor + auth
        run_p2p(
            args[1],
            [] if args[2] == ':' else args[2].split(':')[1:-1],
            encrypt=args[3] == '1',
            priv_key=args[4],
            my_cookie=args[5],
            other_cookies=None if args[6] == '|' else args[6].split('|')[1:-1]
        )
