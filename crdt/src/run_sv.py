import sys

from network.clsv_server import CLSVServer

if __name__ == '__main__':
    args = sys.argv
    h = args[1]
    p = int(args[2])
    encrypt = args[3]
    CLSVServer(h, p, encrypt == '1').listen()
