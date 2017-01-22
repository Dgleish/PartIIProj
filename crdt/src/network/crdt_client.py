import logging
import pickle
import socket
import struct


class CRDTClient(object):
    def __init__(self, puid):
        self.puid = puid

    def recvall(self, sock, cipher=None):
        # make sure you receive `length` bytes of data
        length_struct = sock.recv(4)
        if length_struct is None:
            raise socket.error
        length, = struct.unpack('!I', length_struct)

        buf = ''
        try:
            while length:
                newbuf = sock.recv(length)
                if not newbuf:
                    return None
                buf += newbuf
                length -= len(newbuf)
            if cipher is not None:
                buf = cipher.decrypt(buf)
                buf = buf[:-ord(buf[-1])]

            return pickle.loads(buf)
        except socket.error as e:
            logging.error('{} had socket error {}'.format(self.puid, e))
        except pickle.UnpicklingError as e:
            logging.error('Failed to unpickle {}'.format(e.message))
            raise socket.error()
        except IndexError as e:
            logging.error('weird index error unpickling {}'.format(e.message))
            raise socket.error()

    def pack_and_send(self, unpickled_data, sock, cipher=None):
        # serialise data and send along with its length
        pickled_data = pickle.dumps(unpickled_data)
        if cipher is not None:
            length = 16 - (len(pickled_data) % 16)
            pickled_data += chr(length) * length
            pickled_data = cipher.encrypt(pickled_data)
        header = struct.pack('!I', len(pickled_data))
        sock.sendall(header + pickled_data)

    def connect(self):
        pass

    def send_op(self, op):
        pass
