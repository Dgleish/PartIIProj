from threading import RLock

from wrapt import decorator


@decorator
def synchronized(wrapped, instance, args, kwargs):
    if instance is None:
        context = vars(wrapped)
    else:
        context = vars(instance)

    lock = context.get('_synchronized_lock', None)

    if lock is None:
        lock = context.setdefault('_synchronized_lock', RLock())

    with lock:
        return wrapped(*args, **kwargs)

# Testable
# noinspection PyArgumentList
class ConnectedPeers(object):
    def __init__(self):
        self.peers = {}

    def is_empty(self):
        return len(self.peers) == 0

    @synchronized
    def remove_peer(self, peer):
        del self.peers[peer]

    @synchronized
    def remove_all(self):
        self.peers = {}

    @synchronized
    def add_peer(self, peer, sock, enc_cipher=None, dec_cipher=None):
        self.peers[peer] = {
            'sock': sock,
            'enc_cipher': enc_cipher,
            'dec_cipher': dec_cipher
        }

    @synchronized
    def get_sock_for_peer(self, peer):
        sock = self.peers[peer]
        return sock

    @synchronized
    def get_ciphers_for_peer(self, peer):
        enc_cipher = self.peers[peer]['enc_cipher']
        dec_cipher = self.peers[peer]['dec_cipher']
        return enc_cipher, dec_cipher

    @synchronized
    def iterate_sockets(self):
        for peer, val in self.peers.iteritems():
            yield (peer, val['sock'])

    @synchronized
    def iterate(self):
        for peer, val in self.peers.iteritems():
            yield (peer, val)
