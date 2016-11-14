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
        self.op_q = op_queue
        self.op_q_sem = op_queue_sem
        self.uid = uid

    def connect(self):
        t = threading.Thread(target=self.listen_for_ops)
        t.daemon = True
        t.start()

    @staticmethod
    def recvall(sock, count):
        buf = ''
        while count:
            newbuf = sock.recv(count)
            if not newbuf:
                return None
            buf += newbuf
            count -= len(newbuf)
        return buf

    def listen_for_ops(self):
        self.sock.connect((self.host, self.port))
        while True:
            lengthbuf = self.sock.recv(4)
            length, = struct.unpack('!I', lengthbuf)
            op = self.recvall(self.sock, length)
            # logging.debug('{} UNPARSED got op'.format(self.uid))
            try:
                unpickled_op = pickle.loads(op)
                # logging.debug('{} got op {}'.format(self.uid, unpickled_op))
                self.op_q.put(unpickled_op)
                self.op_q_sem.release()
            except pickle.UnpicklingError as e:
                logging.error('Failed to unpickle {} {}'.format(op, e.message))
                return
            except IndexError as e:
                logging.error('weird index error unpickling {} {}'.format(op, e.message))
                return

    def send_op(self, op):
        # logging.debug('{} sending operation'.format(self.uid))
        self.sock.send(pickle.dumps(op))

    def close(self):
        self.sock.close()
