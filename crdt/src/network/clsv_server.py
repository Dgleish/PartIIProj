import logging
import socket
import threading
from logging.config import fileConfig

from crdt.clock_id import ClockID
from crdt.ops import RemoteOp
from crdt.vector_clock import VectorClock
from network.network_client import NetworkClient, pack_and_send, recvall
from tools.connected_peers import ConnectedPeers
from tools.operation_store import OperationStore

fileConfig('../logging_config.ini')


class CLSVServer(NetworkClient):
    def __init__(self, host, port, encrypt):
        # Operations performed by clients
        logging.debug('{} {} {}'.format(host, port, encrypt))
        self.stored_ops = OperationStore(list)
        self.seen_ops_vc = VectorClock(ClockID('SERVER'))

        super(CLSVServer, self).__init__(self.seen_ops_vc, self.stored_ops, 'SERVER', encrypt)
        self.host = host
        self.port = port

        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', port))

        # connected clients
        self.clients = ConnectedPeers()

    def disconnect_from_client(self, addr, sock, cipher):
        try:
            self.clients.remove_peer(addr)
            pack_and_send('\x00', sock, cipher)
            sock.close()
        except socket.error as e:
            pass

    def listen(self):

        self.sock.listen(5)

        while True:
            try:
                # block until client connects
                logging.debug('listening for connections on port {}'.format(self.port))
                sock, addr = self.sock.accept()
                logging.info('client connected from {}'.format(addr))

                # start new thread calling handle_client
                t = threading.Thread(target=self.handle_client, args=(sock, addr))
                t.daemon = True
                t.start()
            except socket.error as e:
                logging.warning('socket error {}'.format(e))

    def handle_client(self, sock, addr):
        # send all operations up to this point to the new client
        cipher = None
        try:
            if self.encrypt:
                cipher = self.do_DH(sock)

            self.sync_ops_req(sock, cipher)
            self.sync_ops(sock, cipher)
            # add this client to the connected clients
            self.clients.add_peer(addr, sock, cipher)
            while True:
                # get length of next message which will be an int
                op = recvall(sock, cipher)
                logging.debug('received operation {}'.format(op))
                if not isinstance(op, RemoteOp):
                    raise socket.error('Received garbled operation')
                # add this to the list of operations performed
                self.stored_ops.add_op(op.op_id.puid, op)

                if not (self.seen_ops_vc < op.vertex_id):
                    self.seen_ops_vc.update(op)

                # for all other connected clients, send this operation
                peers_to_remove = []
                for ad, cl_dict in self.clients.iterate():
                    if ad != addr:
                        try:
                            pack_and_send(op, cl_dict['sock'], cl_dict['cipher'])
                        except socket.error as e:
                            logging.debug('closing connection to {} {}'.format(addr, e))
                            peers_to_remove.append((ad, sock, cipher))
                            continue

                for (a, s, c) in peers_to_remove:
                    self.disconnect_from_client(a, s, c)

        except socket.error as e:
            logging.debug('closing connection to {} {}'.format(addr, e))
            self.disconnect_from_client(addr, sock, cipher)
            return
