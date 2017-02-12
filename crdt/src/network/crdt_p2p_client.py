import logging
import pickle
import socket
import struct
import threading

import socks

from crdt.crdt_ops import RemoteCRDTOp
from crdt.vector_clock import VectorClock
from network.crdt_network_client import CRDTNetworkClient
from tools.connected_peers import ConnectedPeers
from tools.operation_queue import OperationQueue
from tools.operation_store import OperationStore


class CRDTP2PClient(CRDTNetworkClient):
    def __init__(
            self, port, op_q: OperationQueue, can_consume_sem,
            puid, seen_ops_vc: VectorClock, stored_ops: OperationStore,
            encrypt, known_peers, my_addr, use_tor):
        super(CRDTP2PClient, self).__init__(seen_ops_vc, stored_ops, puid, encrypt)
        self.connected_peers = ConnectedPeers()
        self.connecting_peers = ConnectedPeers()
        self.port = port
        self.op_q = op_q
        self.can_consume_sem = can_consume_sem
        self.known_peers = known_peers
        self.seen_ops_vc = seen_ops_vc
        self.stored_ops = stored_ops
        self.running = False

        self.my_addr = my_addr

        if use_tor:
            socks.set_default_proxy(socks.SOCKS5, "localhost", port=9050)
        self.use_tor = use_tor

        self.add_peer_lock = threading.RLock()

    def remove_peer(self, ip, sock):
        """
        Close connection to peer and note that no longer connected
        """
        try:
            # Send something so that the listening thread gets woken up and can close
            self.pack_and_send('\x00', sock)
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

    def do_p2p_protocol(self, sock, peer_ip, encrypt):
        """
        Generate key and synchronise operations with the peer
        """
        cipher = None

        try:
            if encrypt:
                logging.debug('Doing DH with {}'.format(peer_ip))
                cipher = self.do_DH(sock)
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

    def disconnect(self):
        """
        Close connections to all peers.
        Then make quick connection to self to stop listening for incoming connections
        """
        logging.debug('disconnecting')
        self.can_consume_sem.acquire()
        peers_to_remove = []
        for ip, sock in self.connected_peers.iterate_sockets():
            peers_to_remove.append((ip, sock))
        logging.debug('about to remove {}'.format(peers_to_remove))
        for ip, sock in peers_to_remove:
            self.remove_peer(ip, sock)

        s = socket.socket(socket.AF_INET,
                          socket.SOCK_STREAM)
        s.connect(("localhost", self.port))
        self.running = False
        s.close()
        self.recvsock.close()
        self.can_consume_sem.release()

    def connect(self):
        """
        Connect to all known addresses
        """

        logging.debug('connecting')
        # Force the app to stop applying operations until done connecting
        self.can_consume_sem.acquire()
        self.running = True
        encrypt = self.encrypt
        use_tor = self.use_tor

        # start listening for other peers connecting
        listen_thread = threading.Thread(target=self.listen_for_peers, args=(self.port, encrypt))
        listen_thread.daemon = True
        listen_thread.start()

        for peer_ip in self.known_peers:
            try:
                logging.debug('trying to connect to {} out of {}'.format(peer_ip, self.known_peers))
                self.add_peer_lock.acquire()
                if self.connected_peers.contains(peer_ip) or (
                        self.connecting_peers.contains(peer_ip)):
                    logging.debug('already connected to {}'.format(peer_ip))
                    continue
                if use_tor:
                    sock = socks.socksocket()
                    logging.debug('connecting to {} over Tor'.format(peer_ip + '.onion'))
                    sock.connect((peer_ip + '.onion', self.port))
                else:
                    sock = socket.socket()
                    sock.connect((peer_ip, self.port))
                logging.debug('connected to {}'.format(peer_ip))
                self.pack_and_send(self.my_addr, sock)
                self.connecting_peers.add_peer(peer_ip, sock)

            except (socket.error, struct.error, socks.SOCKS5Error) as e:
                logging.warning('couldn\'t connect to {}, {}'.format(peer_ip, e))
                continue
            finally:
                self.add_peer_lock.release()
                # logging.debug('released add peer lock')

            self.do_p2p_protocol(sock, peer_ip, encrypt)
            logging.debug('finished connecting to {}'.format(peer_ip))

        self.can_consume_sem.release()

    def listen_for_peers(self, port, encrypt):
        """
        Start listening for incoming peer connections
        :param port: the port to listen on
        :param encrypt: Boolean whether or not to encrypt communication
        """
        self.recvsock = socket.socket()
        self.recvsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.recvsock.bind(('', port))
        self.recvsock.listen(100)
        logging.info('listening for peers on port {}'.format(port))

        while self.running:
            try:
                sock, _ = self.recvsock.accept()
                peer_addr = self.recvall(sock)

            except (socket.error, struct.error) as e:
                logging.warning('couldn\'t connect to peer, {}'.format(e))
                continue
            logging.info('peer connected from {}'.format(peer_addr))

            self.add_peer_lock.acquire()
            if (self.connected_peers.contains(peer_addr) or (
                    self.connecting_peers.contains(peer_addr))) and (
                        peer_addr > self.my_addr
            ):
                logging.debug('already connected to {}, dropping'.format(peer_addr))
                self.add_peer_lock.release()
                sock.close()
                continue
            self.connecting_peers.add_peer(peer_addr, sock)
            self.add_peer_lock.release()

            self.do_p2p_protocol(sock, peer_addr, encrypt)

    def listen_for_ops(self, peer_ip, sock, cipher):
        """
        Start receiving operations
        :param peer_ip: the address to receive from
        :param sock: the socket to receive on
        :param cipher: the crypto object
        """
        while True:
            try:
                op = self.recvall(sock, cipher)
                if not isinstance(op, RemoteCRDTOp):
                    logging.warning('op {} was garbled, disconnecting from {}'.format(
                        op, peer_ip
                    ))
                    raise socket.error('Garbled operation')
                logging.debug('{} got op {}'.format(self.puid, op))

                # Note that we've received this
                if not (self.seen_ops_vc < op.vertex_id):
                    # We have seen the vertex this operation references
                    self.seen_ops_vc.update(op)

                # add to the operation queue and signal something has been added
                self.op_q.appendleft(op)

            except (socket.error, pickle.UnpicklingError, IndexError, ValueError) as e:
                logging.warning('Failed to receive op from {} {}'.format(peer_ip, e))
                self.remove_peer(peer_ip, sock)
                return
