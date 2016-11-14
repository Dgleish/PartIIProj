import logging
import pickle
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
        self.clients = {}
        self.clients_lock = threading.Lock()
        self.stored_ops = []
        self.stored_ops_lock = threading.Lock()

    def listen(self):
        self.sock.listen(5)
        while True:
            client, addr = self.sock.accept()
            logger.info('client connected from {}'.format(addr))

            self.clients_lock.acquire()
            # add this client to the connected clients
            self.clients[addr] = client
            self.clients_lock.release()

            # start new thread calling handle_client
            t = threading.Thread(target=self.handle_client, args=(client, addr))
            t.daemon = True
            t.start()

    @staticmethod
    def send_op(client, op):
        # tell the client how long it is so we can delimit the stream
        header = struct.pack('!I', len(op))
        client.send(header + op)

    def handle_client(self, client, addr):
        self.stored_ops_lock.acquire()
        # TODO: make threadsafe iterable thing for stored_ops
        for o in self.stored_ops:
            logger.debug('intial send op {} to {}'.format(o, addr))
            self.send_op(client, o)
        self.stored_ops_lock.release()
        while True:
            try:
                op = client.recv(1024)
                if not op:
                    logger.debug('op was null, closing connection')
                    raise socket.error
                logger.debug('received operation {}'.format(pickle.loads(op)))

                self.stored_ops_lock.acquire()
                self.stored_ops.append(op)
                self.stored_ops_lock.release()

                self.clients_lock.acquire()
                # TODO: make threadsafe iterable thing for other_clients
                for ad, cl in self.clients.iteritems():
                    # send to all other clients
                    if ad != addr:
                        logger.debug('sending op to {}'.format(ad))
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
