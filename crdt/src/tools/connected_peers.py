from tools.decorators import synchronized


# noinspection PyArgumentList
class ConnectedPeers(object):
    def __init__(self):
        self.peers = {}

    @synchronized
    def contains(self, peer):
        return peer in self.peers

    @synchronized
    def is_empty(self):
        return len(self.peers) == 0

    @synchronized
    def remove_peer(self, peer):
        if peer in self.peers:
            del self.peers[peer]

    @synchronized
    def remove_all(self):
        self.peers = {}

    @synchronized
    def add_peer(self, peer, sock, cipher=None):
        self.peers[peer] = {
            'sock': sock,
            'cipher': cipher,
        }

    @synchronized
    def get_sock_for_peer(self, peer):
        sock = self.peers[peer]['sock']
        return sock

    @synchronized
    def get_cipher_for_peer(self, peer):
        cipher = self.peers[peer]['cipher']
        return cipher

    @synchronized
    def iterate_sockets(self):
        return {(peer, val['sock']) for peer, val in self.peers.items()}

    @synchronized
    def iterate(self):
        return self.peers.items()

    @synchronized
    def __repr__(self):
        return 'ConnectedPeers({})'.format(self.peers)
