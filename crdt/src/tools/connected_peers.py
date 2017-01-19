from threading import Lock


# Testable
class ConnectedPeers(object):
    def __init__(self):
        self.peers = {}
        self.lock = Lock()

    def is_empty(self):
        return len(self.peers) == 0

    def remove_peer(self, peer):
        self.lock.acquire()
        del self.peers[peer]
        self.lock.release()

    def remove_all(self):
        self.lock.acquire()
        self.peers = {}
        self.lock.release()

    def add_peer(self, peer, val):
        self.lock.acquire()
        self.peers[peer] = val
        self.lock.release()

    def get_peer(self, peer):
        self.lock.acquire()
        val = self.peers[peer]
        self.lock.release()
        return val

    def iterate(self):
        self.lock.acquire()
        for peer, val in self.peers.iteritems():
            yield (peer, val)
        self.lock.release()
