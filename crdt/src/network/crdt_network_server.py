import logging
import socket
import struct
import threading
from logging.config import fileConfig

fileConfig('../logging_config.ini')
logger = logging.getLogger(__name__)


class CRDTServer(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((host, port))

        # hash table of connected clients
        self.clients = {}
        self.clients_lock = threading.Lock()

        # Operations performed by clients
        self.stored_ops = []
        self.stored_ops_lock = threading.Lock()

    def listen(self):

        self.sock.listen(5)

        while True:
            # block until client connects
            client, addr = self.sock.accept()
            logger.info('client connected from {}'.format(addr))

            # add this client to the connected clients
            self.clients_lock.acquire()
            self.clients[addr] = client
            self.clients_lock.release()

            # start new thread calling handle_client
            t = threading.Thread(target=self.handle_client, args=(client, addr))
            t.daemon = True
            t.start()

    @staticmethod
    def send_op(sock, op):
        # tell the client how long it is so we can delimit the stream
        header = struct.pack('!I', len(op))
        sock.sendall(header + op)

    @staticmethod
    def recvall(sock, length):
        # repeatedly call receive until we get all the data
        buf = ''
        try:
            while length:
                newbuf = sock.recv(length)
                if not newbuf:
                    return None
                buf += newbuf
                length -= len(newbuf)
            return buf
        except socket.error as e:
            logging.error('server had socket error {}'.format(e))

    def handle_client(self, client, addr):
        # send all operations up to this point to the new client
        self.stored_ops_lock.acquire()
        for o in self.stored_ops:
            self.send_op(client, o)
        self.stored_ops_lock.release()

        while True:
            try:
                # get length of next message which will be an int
                lengthbuf = client.recv(4)
                if not lengthbuf:
                    raise socket.error
                length, = struct.unpack('!I', lengthbuf)

                op = self.recvall(client, length)
                logger.debug('received operation {}'.format(op))

                # add this to the list of operations performed
                self.stored_ops_lock.acquire()
                self.stored_ops.append(op)
                self.stored_ops_lock.release()

                # for all other connected clients, send this operation
                self.clients_lock.acquire()
                for ad, cl in self.clients.items():
                    if ad != addr:
                        self.send_op(cl, op)
                self.clients_lock.release()

            except socket.error:
                client.close()
                # remove client from clients dict
                try:
                    del self.clients[addr]
                except KeyError:
                    logger.error("client didn't exist in clients: {}".format(self.clients))
                return


if __name__ == '__main__':
    h = socket.gethostname()
    p = 12346
    CRDTServer(h, p).listen()
