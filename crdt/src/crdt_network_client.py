import logging
import pickle
import socket
import struct
import threading
from logging.config import fileConfig

from crdt_client import CRDTClient

fileConfig('../logging_config.ini')


class CRDTNetworkClient(CRDTClient):
    def __init__(self, host, port, op_queue, puid, seen_ops_vc):
        super(CRDTNetworkClient, self).__init__(puid)
        self.sock = socket.socket()
        self.host = host
        self.port = port

        # local queue of operations to add to
        self.op_q = op_queue

        self.puid = puid

        self.connected_sem = threading.Semaphore(0)
        self.is_connected = False

    def connect(self):
        t = threading.Thread(target=self.listen_for_ops)
        t.daemon = True
        t.start()

    #     TODO: reconnect if unexpected disconnect

    def listen_for_ops(self):
        try:
            self.sock.connect((self.host, self.port))
            self.connected_sem.release()
            self.is_connected = True
        except socket.error as e:
            logging.error('Socket connection error {}'.format(e))

        while True:
            # get length of next operation
            lengthbuf = self.sock.recv(4)
            if lengthbuf is None:
                return
            length, = struct.unpack('!I', lengthbuf)

            op = self.recvall(self.sock, length)

            try:
                unpickled_op = pickle.loads(op)
                # logging.debug('{} got op {}'.format(self.puid, unpickled_op))

                # add to the operation queue and signal something has been added
                self.op_q.appendleft(unpickled_op)
            except pickle.UnpicklingError as e:
                logging.error('Failed to unpickle {} {}'.format(op, e.message))
                return
            except IndexError as e:
                logging.error('weird index error unpickling {} {}'.format(op, e.message))
                return

    def send_op(self, unpickled_op):
        # logging.debug('{} sending operation'.format(self.puid))
        # if we haven't connected up the socket yet, wait until we have
        if not self.is_connected:
            self.connected_sem.acquire()

        self.pack_and_send(unpickled_op, self.sock)

    def close(self):
        logging.debug('{} closing socket'.format(self.puid))
        self.sock.close()
