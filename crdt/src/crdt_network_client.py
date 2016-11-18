import logging
import pickle
import socket
import struct
import threading
from logging.config import fileConfig

from crdt_network import CRDTNetwork

fileConfig('../logging_config.ini')


class CRDTNetworkClient(CRDTNetwork):
    def __init__(self, host, port, op_queue, op_queue_sem, uid):
        self.sock = socket.socket()
        self.host = host
        self.port = port

        # local queue of operations to add to
        self.op_q = op_queue
        self.op_q_sem = op_queue_sem

        self.uid = uid

        self.connected_sem = threading.Semaphore(0)
        self.is_connected = False

    def connect(self):
        t = threading.Thread(target=self.listen_for_ops)
        t.daemon = True
        t.start()

    def recvall(self, sock, length):
        # make sure you receive `length` bytes of data
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
            logging.error('{} had socket error {}'.format(self.uid, e))

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
                # logging.debug('{} got op {}'.format(self.uid, unpickled_op))

                # add to the operation queue and signal something has been added
                self.op_q.appendleft(unpickled_op)
                self.op_q_sem.release()
            except pickle.UnpicklingError as e:
                logging.error('Failed to unpickle {} {}'.format(op, e.message))
                return
            except IndexError as e:
                logging.error('weird index error unpickling {} {}'.format(op, e.message))
                return

    def send_op(self, unpickled_op):
        # logging.debug('{} sending operation'.format(self.uid))
        # if we haven't connected up the socket yet, wait until we have
        if not self.is_connected:
            self.connected_sem.acquire()

        # serialise operation and send along with its length
        pickled_op = pickle.dumps(unpickled_op)
        header = struct.pack('!I', len(pickled_op))
        self.sock.sendall(header + pickled_op)

    def close(self):
        logging.debug('{} closing socket'.format(self.uid))
        self.sock.close()
