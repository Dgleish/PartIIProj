import logging
import pickle
import socket
import struct


class CRDTClient(object):
    def __init__(self, puid):
        self.puid = puid

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
            logging.error('{} had socket error {}'.format(self.puid, e))

    def pack_and_send(self, unpickled_data, sock):
        # serialise data and send along with its length
        pickled_data = pickle.dumps(unpickled_data)
        header = struct.pack('!I', len(pickled_data))
        sock.sendall(header + pickled_data)

    def connect(self):
        pass

    def send_op(self, op):
        pass
