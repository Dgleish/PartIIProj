import logging
import pickle
import socket
import struct
import threading

from crdt.crdt_ops import CRDTOp
from crdt_client import CRDTClient
from crypto.DiffieHellman import DiffieHellman
from tools.cipher import Cipher
from tools.connected_peers import ConnectedPeers


class CRDTP2PClient(CRDTClient):
    def __init__(self, host, port, op_q, puid, seen_ops_vc, stored_ops, known_peers):
        super(CRDTP2PClient, self).__init__(puid)
        self.connected_peers = ConnectedPeers()
        self.connecting_peers = ConnectedPeers()
        self.hostname = host
        self.port = port
        self.op_q = op_q
        self.known_peers = known_peers
        self.seen_ops_vc = seen_ops_vc
        self.stored_ops = stored_ops
        self.running = False
        self.my_DH = DiffieHellman()
        self.add_peer_lock = threading.RLock()

    def remove_peer(self, ip, sock):
        """
        Close connection to peer and note that no longer connected
        """
        try:
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
        except:
            pass
        logging.debug('closed socket for {}'.format(ip))
        self.connected_peers.remove_peer(ip)

    def send_op(self, unpickled_op):
        """
        Send operation to all connected peers
        :param unpickled_op: the operation to send
        """
        peers_to_remove = []
        for peer_ip, peer_info in self.connected_peers.iterate():
            try:
                self.pack_and_send(unpickled_op, peer_info['sock'], peer_info['cipher'])
            except socket.error:
                # If fail to send, assume disconnected
                logging.debug('error sending to {}, going to remove'.format(peer_ip))
                peers_to_remove.append((peer_ip, peer_info['sock']))

        for ip, sock in peers_to_remove:
            self.remove_peer(ip, sock)

    def sync_ops_req(self, sock, cipher):
        """
        send clock of which ops I have
        :param cipher: the crypto object
        :param sock: socket to send to
        """
        self.pack_and_send(self.seen_ops_vc, sock, cipher)

    def sync_ops(self, sock, cipher):
        """
        receive clock of which ops they have
        :param sock: socket object to receive from
        :param cipher: the crypto object
        """
        their_vc = self.recvall(sock, cipher)
        # determine which ops to send
        ops_to_send = self.stored_ops.determine_ops(their_vc)
        # logging.debug('sync ops sending over {}'.format(ops_to_send))
        for op in ops_to_send:
            self.pack_and_send(op, sock, cipher)

    def do_p2p_protocol(self, sock, peer_ip, encrypt=True):
        """
        Generate key and synchronise operations with the peer
        """
        cipher = None

        try:
            if encrypt:
                logging.debug('Doing DH with {}'.format(peer_ip))
                # send public key
                self.pack_and_send(self.my_DH.publicKey, sock)

                # receive other public key
                other_key = self.recvall(sock)

                # generate shared secret
                key = self.my_DH.genKey(other_key)

                cipher = Cipher(key)
                logging.debug('cipher ready for {}'.format(peer_ip))

            # synchronise operations
            logging.debug('requesting sync ops with {}'.format(peer_ip))
            self.sync_ops_req(sock, cipher)
            logging.debug('requested sync ops with {}'.format(peer_ip))
            self.sync_ops(sock, cipher)
            logging.debug('synced ops with {}'.format(peer_ip))

            # Note that we're connected to this peer
            self.connected_peers.add_peer(peer_ip, sock, cipher)
            self.connecting_peers.remove_peer(peer_ip)

        except socket.error as e:
            self.connecting_peers.remove_peer(peer_ip)
            logging.error('failed to do protocol with {} {}'.format(peer_ip, e))
            return

        logging.debug('starting op thread for {}'.format(peer_ip))
        # start listening for other operations from this peer
        op_thread = threading.Thread(target=self.listen_for_ops, args=(peer_ip, sock, cipher))
        op_thread.daemon = True
        op_thread.start()

    def disconnect(self, can_consume_sem):
        """
        Close connections to all peers.
        Then make quick connection to self to stop listening for incoming connections
        """
        logging.debug('disconnecting')
        can_consume_sem.acquire()
        peers_to_remove = []
        for ip, sock in self.connected_peers.iterate_sockets():
            peers_to_remove.append((ip, sock))
        logging.debug('about to remove {}'.format(peers_to_remove))
        for ip, sock in peers_to_remove:
            self.remove_peer(ip, sock)

        s = socket.socket(socket.AF_INET,
                          socket.SOCK_STREAM)
        s.connect((self.hostname, self.port))
        self.running = False
        s.close()
        self.recvsock.close()
        can_consume_sem.release()

    def connect(self, can_consume_sem):
        """
        Connect to all known addresses
        """
        # Force the app to stop applying operations until done connecting
        logging.debug('connecting')
        can_consume_sem.acquire()
        self.running = True

        # start listening for other peers connecting
        listen_thread = threading.Thread(target=self.listen_for_peers, args=(self.port,))
        listen_thread.daemon = True
        listen_thread.start()

        for peer_ip in self.known_peers:
            # logging.debug('trying to connect to {} out of {}'.format(peer_ip, self.known_peers))
            try:
                self.add_peer_lock.acquire()
                # logging.debug('got add_peer_lock')
                if self.connected_peers.contains(peer_ip) or (
                        self.connecting_peers.contains(peer_ip)):
                    logging.debug('already connected to {}'.format(peer_ip))
                    continue
                sock = socket.socket()
                sock.connect((peer_ip, self.port))
                logging.debug('connected to {}'.format(peer_ip))
                self.connecting_peers.add_peer(peer_ip, sock)

            except (socket.error, struct.error) as e:
                logging.warn('couldn\'t connect to {}, {}'.format(peer_ip, e))
                continue
            finally:
                self.add_peer_lock.release()
                # logging.debug('released add peer lock')

            self.do_p2p_protocol(sock, peer_ip, True)
            logging.debug('finished connecting to {}'.format(peer_ip))

        can_consume_sem.release()

    def listen_for_peers(self, port):
        """
        Start listening for incoming peer connections
        :param port: the port to listen on
        """
        self.recvsock = socket.socket()
        self.recvsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.recvsock.bind(('', port))
        self.recvsock.listen(100)
        logging.info('listening for peers on port {}'.format(port))

        while self.running:
            try:
                sock, (peer_ip, po) = self.recvsock.accept()
                logging.info('peer connected from {}'.format(peer_ip))

            except (socket.error, struct.error) as e:
                logging.warn('couldn\'t connect to peer, {}'.format(e))
                continue

            self.add_peer_lock.acquire()
            # logging.debug('got add_peer_lock')
            if (self.connected_peers.contains(peer_ip) or (
                    self.connecting_peers.contains(peer_ip))) and (
                        peer_ip > self.hostname
            ):
                logging.debug('already conn. {} {}'.format(peer_ip, self.hostname))
                self.add_peer_lock.release()
                # logging.debug('released add peer lock')
                sock.close()
                continue
            self.connecting_peers.add_peer(peer_ip, sock)
            self.add_peer_lock.release()
            # logging.debug('released add peer lock')

            self.do_p2p_protocol(sock, peer_ip, True)

    def listen_for_ops(self, peer_ip, sock, cipher):
        """
        Start receiving operations
        :param peer_ip: the address to receive from
        :param sock: the socket to receive on
        :param cipher: the crypto object
        """
        while True:
            try:
                unpickled_op = self.recvall(sock, cipher)
                if not isinstance(unpickled_op, CRDTOp):
                    logging.warn('op {} was garbled, disconnecting from {}'.format(
                        unpickled_op, peer_ip
                    ))
                    raise socket.error('Garbled operation')
                logging.debug('{} got op {}'.format(self.puid, unpickled_op))

                # Note that we've received this
                self.seen_ops_vc.update(unpickled_op)

                # add to the operation queue and signal something has been added
                self.op_q.appendleft(unpickled_op)

            except (socket.error, pickle.UnpicklingError, IndexError) as e:
                logging.warn('Failed to receive op {} from {}'.format(e.message, peer_ip))
                self.remove_peer(peer_ip, sock)
                return
