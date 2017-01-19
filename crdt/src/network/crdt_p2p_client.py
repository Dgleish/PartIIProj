import logging
import pickle
import socket
import struct
import threading

from crdt_client import CRDTClient


class CRDTP2PClient(CRDTClient):
    def __init__(self, host, port, op_q, puid, seen_ops_vc, stored_ops, known_peers, connected_peers):
        super(CRDTP2PClient, self).__init__(puid)
        self.connected_peers = connected_peers
        self.hostname = host
        self.port = port
        self.op_q = op_q
        self.known_peers = known_peers
        self.seen_ops_vc = seen_ops_vc
        self.stored_ops = stored_ops
        self.running = False

    def remove_peer(self, ip, sock):
        sock.close()
        self.connected_peers.remove_peer(ip)

    def send_op(self, unpickled_op):
        peers_to_remove = []
        for peer_ip, peer_sock in self.connected_peers.iterate():
            try:
                self.pack_and_send(unpickled_op, peer_sock)
            except socket.error:
                peers_to_remove.append((peer_ip, peer_sock))

        for ip, sock in peers_to_remove:
            self.remove_peer(ip, sock)

    def disconnect(self):
        logging.debug('disconnecting')
        for p, sock in self.connected_peers.iterate():
            sock.close()

        s = socket.socket(socket.AF_INET,
                          socket.SOCK_STREAM)
        s.connect((self.hostname, self.port))
        self.running = False
        s.close()
        self.recvsock.close()

    def connect(self):
        logging.debug('connecting')
        self.running = True
        # have listener thread waiting for connections
        # dispatch handler for each connection that comes in
        # thread for sending as well
        for peer_ip in self.known_peers:
            try:
                logging.debug('trying to connect to {}:{}'.format(peer_ip, self.port))
                sock = socket.socket()
                sock.connect((peer_ip, self.port))
                logging.debug('connected to {}'.format(peer_ip))
                self.connected_peers.add_peer(peer_ip, sock)

                # sync up operations with this peer
                logging.debug('sync_ops_req')
                self.sync_ops_req(sock)
                logging.debug('sync_ops')

                self.sync_ops(sock)

                op_thread = threading.Thread(target=self.listen_for_ops, args=(peer_ip, sock))
                op_thread.daemon = True
                op_thread.start()

            except socket.error as e:
                logging.warn('couldn\'t connect to {}, {}'.format(peer_ip, e))
                continue
        listen_thread = threading.Thread(target=self.listen_for_peers, args=(self.hostname, self.port))
        listen_thread.daemon = True
        listen_thread.start()

    def sync_ops_req(self, sock):
        # send clock of which ops I have
        self.pack_and_send(self.seen_ops_vc, sock)

    def sync_ops(self, sock):
        # receive clock of which ops they have
        length_struct = sock.recv(4)
        length, = struct.unpack('!I', length_struct)
        their_vc_pickled = self.recvall(sock, length)
        their_vc = pickle.loads(their_vc_pickled)
        # determine which ops to send
        ops_to_send = self.stored_ops.determine_ops(their_vc)
        logging.debug('sync ops sending over {}'.format(ops_to_send))
        for op in ops_to_send:
            self.pack_and_send(op, sock)

    def listen_for_peers(self, host, port):
        self.recvsock = socket.socket()
        self.recvsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.recvsock.bind(('', port))
        self.recvsock.listen(5)
        print socket.gethostbyname(socket.gethostname())
        while self.running:
            try:
                logging.info('listening for peers on port {}'.format(port))
                sock, address = self.recvsock.accept()
                logging.info('peer connected from {}'.format(address))
                logging.debug('sync_ops_req')
                self.sync_ops_req(sock)
                logging.debug('sync_ops')
                self.sync_ops(sock)
                logging.debug('synced ops with new peer')
            except (socket.error, struct.error):
                continue
            self.connected_peers.add_peer(address, sock)
            op_thread = threading.Thread(target=self.listen_for_ops, args=(address, sock))
            op_thread.daemon = True
            op_thread.start()

    def listen_for_ops(self, peer_ip, sock):

        # make sure to catch socket errors and abort properly
        while True:
            try:
                length_struct = sock.recv(4)
                if length_struct is None:
                    raise socket.error
                length, = struct.unpack('!I', length_struct)
                op = self.recvall(sock, length)

                try:
                    unpickled_op = pickle.loads(op)
                    logging.debug('{} got op {}'.format(self.puid, unpickled_op))
                    self.seen_ops_vc.update(unpickled_op)
                    # add to the operation queue and signal something has been added
                    self.op_q.appendleft(unpickled_op)

                    logging.debug('{} added op {} to queue'.format(self.puid, unpickled_op))

                except pickle.UnpicklingError as e:
                    logging.error('Failed to unpickle {} {}'.format(op, e.message))
                    raise socket.error()
                except IndexError as e:
                    logging.error('weird index error unpickling {} {}'.format(op, e.message))
                    raise socket.error()

            except socket.error:
                self.remove_peer(peer_ip, sock)
                return
