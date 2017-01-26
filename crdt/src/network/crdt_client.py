import pickle
import socket
import struct


class CRDTClient(object):
    def __init__(self, puid):
        self.puid = puid

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

    def connect(self, can_consume_sem):
        pass

    def send_op(self, op):
        pass
