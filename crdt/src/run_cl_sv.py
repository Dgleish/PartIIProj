import sys

from crdt.crdt_ops import CRDTOpAddRightLocal, CRDTOpDeleteLocal
from crdt_app import CRDTApp


def run_cl_sv(my_addr, server_address, port, encrypt=True):
    app = CRDTApp(my_addr.replace('.', '')[-6:], port, my_addr, ops_to_do=[
        CRDTOpAddRightLocal(my_addr[0]), CRDTOpDeleteLocal(),
        CRDTOpAddRightLocal(my_addr[0])
    ], server_address=server_address, encrypt=encrypt)

if __name__ == '__main__':
    args = sys.argv
    print('got args {}'.format(args))
    run_cl_sv(args[1], args[2], int(args[3]), args[4] == '1')
