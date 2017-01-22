import logging
import socket
import struct
import threading

from Crypto.Cipher import AES
from Crypto.Util import Counter

from crdt.crdt_ops import CRDTOp
from crdt_client import CRDTClient
from crypto.DiffieHellman import DiffieHellman


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
        self.my_DH = DiffieHellman()

    def remove_peer(self, ip, sock):
        """
        Close connection to peer and note that no longer connected
        """
        sock.close()
        self.connected_peers.remove_peer(ip)

    def send_op(self, unpickled_op):
        """
        Send operation to all connected peers
        :param unpickled_op: the operation to send
        """
        peers_to_remove = []
        for peer_ip, peer_info in self.connected_peers.iterate():
            try:
                self.pack_and_send(unpickled_op, peer_info['sock'], peer_info['enc_cipher'])
            except socket.error:
                # If fail to send, assume disconnected
                peers_to_remove.append((peer_ip, peer_info['sock']))

        for ip, sock in peers_to_remove:
            self.remove_peer(ip, sock)

    def sync_ops_req(self, sock, enc_cipher):
        """
        send clock of which ops I have
        :param sock: socket to send to
        :param enc_cipher: the encryption object
        """
        self.pack_and_send(self.seen_ops_vc, sock, enc_cipher)

    def sync_ops(self, sock, enc_cipher, dec_cipher):
        """
        receive clock of which ops they have
        :param sock: socket object to receive from
        :param enc_cipher: the encryption object
        :param dec_cipher: the decryption object
        """
        their_vc = self.recvall(sock, dec_cipher)
        # determine which ops to send
        ops_to_send = self.stored_ops.determine_ops(their_vc)
        logging.debug('sync ops sending over {}'.format(ops_to_send))
        for op in ops_to_send:
            self.pack_and_send(op, sock, enc_cipher)

    def disconnect(self):
        """
        Close connections to all peers.
        Then make quick connection to self to stop listening for incoming connections
        """
        logging.debug('disconnecting')
        peers_to_remove = []
        for ip, sock in self.connected_peers.iterate_sockets():
            peers_to_remove.append((ip, sock))

        for ip, sock in peers_to_remove:
            self.remove_peer(ip, sock)

        s = socket.socket(socket.AF_INET,
                          socket.SOCK_STREAM)
        s.connect((self.hostname, self.port))
        self.running = False
        s.close()
        self.recvsock.close()

    def connect(self):
        """
        Connect to all known addresses
        """
        logging.debug('connecting')
        self.running = True
        for peer_ip in self.known_peers:
            try:
                sock = socket.socket()
                sock.connect((peer_ip, self.port))
                logging.debug('connected to {}'.format(peer_ip))

                self.do_p2p_protocol(sock, peer_ip)

            except (socket.error, struct.error) as e:
                logging.warn('couldn\'t connect to {}, {}'.format(peer_ip, e))
                continue

        # start listening for other peers connecting
        listen_thread = threading.Thread(target=self.listen_for_peers, args=(self.port,))
        listen_thread.daemon = True
        listen_thread.start()

    def do_p2p_protocol(self, sock, peer_ip):
        """
        Generate key and synchronise operations with the peer
        """

        # send public key
        self.pack_and_send(self.my_DH.publicKey, sock)

        # receive other public key
        other_key = self.recvall(sock)

        # generate shared secret
        self.my_DH.genKey(other_key)
        key = self.my_DH.getKey()
        # logging.debug('generated key {}'.format(key.encode('hex')))

        # create cipher object from key
        ctr1 = Counter.new(128)
        ctr2 = Counter.new(128)
        enc_cipher = AES.new(key, AES.MODE_CTR, counter=ctr1)
        dec_cipher = AES.new(key, AES.MODE_CTR, counter=ctr2)

        # synchronise operations
        self.sync_ops_req(sock, enc_cipher)
        self.sync_ops(sock, enc_cipher, dec_cipher)
        logging.debug('synced ops with new peer')

        # Note that we're connected to this peer
        self.connected_peers.add_peer(peer_ip, sock, enc_cipher, dec_cipher)

        # start listening for other operations from this peer
        op_thread = threading.Thread(target=self.listen_for_ops, args=(peer_ip, sock, dec_cipher))
        op_thread.daemon = True
        op_thread.start()

    def listen_for_peers(self, port):
        """
        Start listening for incoming peer connections
        :param port: the port to listen on
        """
        self.recvsock = socket.socket()
        self.recvsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.recvsock.bind(('', port))
        self.recvsock.listen(5)
        logging.info('listening for peers on port {}'.format(port))

        while self.running:
            try:
                sock, peer_ip = self.recvsock.accept()
                logging.info('peer connected from {}'.format(peer_ip))

                self.do_p2p_protocol(sock, peer_ip)

            except (socket.error, struct.error) as e:
                logging.warn('couldn\'t connect to peer, {}'.format(e))
                continue

    def listen_for_ops(self, peer_ip, sock, dec_cipher):
        """
        Start receiving operations
        :param peer_ip: the address to receive from
        :param sock: the socket to receive on
        :param dec_cipher: the decryption object
        """
        while True:
            try:
                unpickled_op = self.recvall(sock, dec_cipher)
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

            except socket.error:
                self.remove_peer(peer_ip, sock)
                return
