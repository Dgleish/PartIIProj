import logging
import pickle
import socket
import struct

from crdt.vector_clock import VectorClock
from crypto.DiffieHellman import DiffieHellman
from crypto.cipher import Cipher


class CRDTNetworkClient(object):
    def __init__(self, seen_ops_vc, stored_ops, puid, encrypt=False):
        self.seen_ops_vc = seen_ops_vc
        self.stored_ops = stored_ops
        self.puid = puid
        self.encrypt = encrypt
        self.can_send = True
        if encrypt:
            self.my_DH = DiffieHellman()

    def recvall(self, sock, cipher=None):
        # make sure you receive `length` bytes of data
        length_struct = sock.recv(4)
        if not length_struct:
            raise socket.error
        length, = struct.unpack('!I', length_struct)

        buf = []
        while length:
            newbuf = sock.recv(length)
            if not newbuf:
                return None
            buf.append(newbuf)
            length -= len(newbuf)
        if len(buf) == 0:
            raise socket.error('No data received')
        else:
            buf = b''.join(buf)
        if cipher is not None:
            buf = cipher.decrypt2(buf)

        return pickle.loads(buf)

    def pack_and_send(self, unpickled_data, sock, cipher=None):
        # serialise data and send along with its length
        pickle_func = getattr(unpickled_data, "pickle", None)
        if pickle_func is None:
            pickled_data = pickle.dumps(unpickled_data)
        else:
            pickled_data = unpickled_data.pickle()
        if cipher is not None:
            pickled_data = cipher.encrypt2(pickled_data)
        header = struct.pack('!I', len(pickled_data))
        sock.sendall(header + pickled_data)

    def connect(self):
        pass

    def disconnect(self):
        pass

    def send_op(self, op):
        pass

    def sync_ops_req(self, sock, cipher):
        """
        send clock of which ops I have
        :param cipher: the crypto object
        :param sock: socket to send to
        """
        # logging.debug('sending {}'.format(self.seen_ops_vc))
        self.pack_and_send(self.seen_ops_vc, sock, cipher)

    def sync_ops(self, sock, cipher):
        """
        receive clock of which ops they have
        :param sock: socket object to receive from
        :param cipher: the crypto object
        """

        their_vc = self.recvall(sock, cipher)
        # logging.debug('got vector clock {}'.format(their_vc))
        assert isinstance(their_vc, VectorClock)
        # determine which ops to send
        ops_to_send = self.stored_ops.determine_ops_after_vc(their_vc)
        logging.debug('sync ops sending over {}'.format(ops_to_send))
        for op in ops_to_send:
            self.pack_and_send(op, sock, cipher)
            # MEASUREMENTS
            # if self.can_send:
            #     self.can_send = False
            #     for op in ops_to_send:
            #         sleep(0.1)
            #         self.pack_and_send(op, sock, cipher)
            #         t = perf_counter()
            #         with open(self.puid, 'a') as f:
            #             f.write('{}\n'.format(t))


    def do_DH(self, sock):
        # send public key
        self.pack_and_send(self.my_DH.publicKey, sock)

        # receive other public key
        other_key = self.recvall(sock)

        # generate shared secret
        key = self.my_DH.genKey(other_key)

        return Cipher(key)
