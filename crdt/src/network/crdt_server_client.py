import logging
import pickle
import socket
import threading

from crdt.crdt_ops import RemoteCRDTOp
from network.crdt_network_client import CRDTNetworkClient, pack_and_send, recvall


class CRDTServerClient(CRDTNetworkClient):
    def __init__(self, server_port, op_queue, can_consume_sem,
                 puid, seen_ops_vc, stored_ops, encrypt, server_address):
        super(CRDTServerClient, self).__init__(seen_ops_vc, stored_ops, puid, encrypt)

        self.server_address = server_address
        self.server_port = server_port

        # local queue of operations to add to
        self.op_q = op_queue

        self.seen_ops_vc = seen_ops_vc

        self.is_connected = False

        self.can_consume_sem = can_consume_sem

    def send_op(self, unpickled_op):
        if self.is_connected:
            logging.debug('sending op {}'.format(unpickled_op))
            pack_and_send(unpickled_op, self.sock, self.cipher)

    def connect(self):
        logging.debug('connecting to server at {} {}'.format(
            self.server_address, self.server_port
        ))
        self.can_consume_sem.acquire()
        try:
            self.sock = socket.socket()
            self.sock.connect((self.server_address, self.server_port))
            self.is_connected = True
            logging.debug('connected to server'.format())

            self.cipher = None
            if self.encrypt:
                self.cipher = self.do_DH(self.sock)

            self.sync_ops_req(self.sock, self.cipher)
            self.sync_ops(self.sock, self.cipher)

            t = threading.Thread(target=self.listen_for_ops)
            t.daemon = True
            t.start()
        except socket.error as e:
            logging.error('Socket connection error {}'.format(e))
        finally:
            self.can_consume_sem.release()

    def disconnect(self):
        self.can_consume_sem.acquire()
        try:
            pack_and_send('\x00', self.sock, self.cipher)
            self.sock.close()
            self.is_connected = False
        except socket.error as e:
            pass
        finally:
            self.can_consume_sem.release()

    def listen_for_ops(self):

        while True:
            try:
                op = recvall(self.sock, self.cipher)
                if not isinstance(op, RemoteCRDTOp):
                    raise socket.error('Received garbled operation')

                # Note that we've received this only if it references something we've seen
                if not (self.seen_ops_vc < op.vertex_id):
                    self.seen_ops_vc.update(op)

                logging.debug('{} got op {}'.format(self.puid, op))

                # add to the operation queue and signal something has been added
                self.op_q.appendleft(op)

            except (socket.error, pickle.UnpicklingError, IndexError) as e:
                logging.error('Failed to receive op {}'.format(e))
                self.disconnect()
                return
