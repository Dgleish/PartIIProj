import logging
import pickle
import socket
import struct
import threading
from time import perf_counter

import socks

from crdt.ops import RemoteOp
from crdt.vector_clock import VectorClock
from network.network_client import NetworkClient, pack_and_send, recvall
from tools.connected_peers import ConnectedPeers
from tools.operation_queue import OperationQueue
from tools.operation_store import OperationStore


class CRDTP2PClient(NetworkClient):
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

        self.filename = puid

        if use_tor:
            socks.set_default_proxy(socks.SOCKS5, "localhost", port=9050)
        self.use_tor = use_tor

        self.add_peer_lock = threading.RLock()

        self.time_file = '{}recv'.format(puid)

    def remove_peer(self, ip, sock):
        """
        Close connection to peer and note that no longer connected
        """
        try:
            # Send something so that the listening thread gets woken up and can close
            pack_and_send('\x00', sock)
            sock.close()
            logging.debug('closed socket for {}'.format(ip))
        except socket.error:
            pass
        self.connected_peers.remove_peer(ip)

    def send_op(self, unpickled_op):
        """
        Send operation to all connected peers
        :param unpickled_op: the operation to send
        """
        peers_to_remove = []
        for peer_ip, peer_info in self.connected_peers.iterate():
            try:
                pack_and_send(unpickled_op, peer_info['sock'], peer_info['cipher'])

            except socket.error:
                # If fail to send, assume disconnected
                logging.debug('error sending to {}, going to remove'.format(peer_ip))
                peers_to_remove.append((peer_ip, peer_info['sock']))

        for ip, sock in peers_to_remove:
            self.remove_peer(ip, sock)

    def do_p2p_protocol(self, sock, peer_ip, encrypt):
        """
        (Generate key) and synchronise operations with the new peer
        """
        cipher = None

        try:
            if encrypt:
                # The application's encryption flag is set
                # Returns object with encrypt()/decrypt() methods
                cipher = self.do_DH(sock)

            # synchronise operations
            # Send your vector clock to them
            self.sync_ops_req(sock, cipher)
            # Receive their vector clock
            # Work out set difference of yours - theirs
            # Send those operations
            self.sync_ops(sock, cipher)

            # Note that we're connected to this peer
            # And no longer in the process of connecting
            self.connected_peers.add_peer(peer_ip, sock, cipher)
            self.connecting_peers.remove_peer(peer_ip)

        except socket.error as e:
            # Communication failure, so stop trying and connect to the next peer
            self.connecting_peers.remove_peer(peer_ip)
            return

        # Start listening for operations from this new peer
        op_thread = threading.Thread(target=self.listen_for_ops,
                                     args=(peer_ip, sock, cipher))
        op_thread.daemon = True
        op_thread.start()

    def disconnect(self):
        """
        Close connections to all peers.
        Then make quick connection to self to stop listening for incoming connections
        """
        logging.debug('disconnecting')
        # MEASUREMENT
        self.can_consume_sem.acquire()
        for ip, val in self.connected_peers.iterate():
            logging.debug('removing peer {}'.format(ip))
            self.remove_peer(ip, val['sock'])

        # force listening socket to close as well
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

        for peer_addr in self.known_peers:
            try:
                logging.debug('trying to connect to {} out of {}'.format(peer_addr, self.known_peers))
                self.add_peer_lock.acquire()
                if self.connected_peers.contains(peer_addr) or (
                        self.connecting_peers.contains(peer_addr)):
                    logging.debug('already connected to {}'.format(peer_addr))
                    continue
                if use_tor:
                    sock = socks.socksocket()
                    logging.debug('connecting to {} over Tor'.format(peer_addr + '.onion'))
                    sock.connect((peer_addr + '.onion', self.port))
                else:
                    sock = socket.socket()
                    sock.connect((peer_addr, self.port))
                logging.debug('connected to {}'.format(peer_addr))
                pack_and_send(self.my_addr, sock)
                self.connecting_peers.add_peer(peer_addr, sock)

            except (socket.error, struct.error, socks.SOCKS5Error) as e:
                logging.warning('couldn\'t connect to {}, {}'.format(peer_addr, e))
                continue
            finally:
                self.add_peer_lock.release()
                # logging.debug('released add peer lock')

            self.do_p2p_protocol(sock, peer_addr, encrypt)
            # MEASUREMENT
            # op_thread = threading.Thread(target=self.listen_for_ops, args=(peer_addr, sock, None))
            # op_thread.daemon = True
            # op_thread.start()
            # LENGTH_MEASUREMENT
            # self.sync_ops(sock, None)
            # break
        # listen_thread.join()

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
                logging.debug('in listening loop')
                sock, _ = self.recvsock.accept()
                peer_addr = recvall(sock)
                logging.info('peer connected from {}'.format(peer_addr))

            except (socket.error, struct.error) as e:
                logging.warning('couldn\'t connect to peer, {}'.format(e))
                continue


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

            # LENGTH MEASUREMENT
            self.do_p2p_protocol(sock, peer_addr, encrypt)
            # self.sync_ops_req(sock, None)
            # self.listen_for_ops(peer_addr, sock, None)
            # return

    def listen_for_ops(self, peer_ip, sock, cipher):
        """
        Start receiving operations
        :param peer_ip: the address to receive from
        :param sock: the socket to receive on
        :param cipher: the crypto object
        """
        ops_done = 0
        with open(self.time_file, 'w+') as f:
            while True:
                try:
                    op = recvall(sock, cipher)
                    logging.debug('{} got op {}'.format(self.puid, op))
                    f.write('{}\n'.format(perf_counter()))
                    ops_done += 1
                    if not isinstance(op, RemoteOp):
                        logging.warning('op {} was garbled, disconnecting from {}'.format(
                            op, peer_ip
                        ))
                        raise socket.error('Garbled operation')


                    # Note that we've received this
                    if not (self.seen_ops_vc < op.vertex_id):
                        # We have seen the vertex this operation references
                        # TODO: for lseq ids the comparison should look at timestamp first instead of postition
                        self.seen_ops_vc.update(op)
                        logging.debug('vc {}'.format(self.seen_ops_vc))

                    # add to the operation queue and signal something has been added
                    # MEASUREMENT
                    self.op_q.appendleft(op)

                    # MEASUREMENT
                    # if ops_done >= 100:
                    #     print('finished')
                    #     f.flush()
                    #     self.disconnect()
                    #     return

                except (socket.error, pickle.UnpicklingError, IndexError, ValueError) as e:
                    logging.warning('Failed to receive op from {} {}'.format(peer_ip, e))
                    self.remove_peer(peer_ip, sock)
                    return
