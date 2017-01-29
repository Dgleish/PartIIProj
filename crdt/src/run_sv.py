import sys

from network.crdt_server import CRDTServer

if __name__ == '__main__':
    args = sys.argv
    h = args[1]
    p = int(args[2])
    encrypt = args[3]
    CRDTServer(h, p, encrypt == '1').listen()
