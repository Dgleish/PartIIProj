import logging
import pickle
from threading import RLock

from wrapt import decorator

from crdt_clock import CRDTClock


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


# noinspection PyArgumentList
class VectorClock(object):
    """ contains most recently seen op from each peer """

    def __init__(self, owner_clock):
        assert isinstance(owner_clock, CRDTClock)
        self.owner_puid = owner_clock.puid
        self.clocks = {self.owner_puid: owner_clock}

    @synchronized
    def __getstate__(self):
        return {
            'owner_puid': self.owner_puid,
            'clocks': self.clocks,
        }

    @synchronized
    def __setstate__(self, state):
        self.owner_puid = state['owner_puid']
        self.clocks = state['clocks']
        # recreate lock, don't copy it from other place

    @synchronized
    def get_clock(self, puid):
        """
        :param puid: The ID of the peer
        :return: Clock associated with this peer
        """
        val = None
        if puid in self.clocks:
            val = self.clocks[puid]
        return val

    @synchronized
    def update(self, op):
        """
        Increment the corresponding clock for this operation
        """
        op_id = op.op_id
        other_puid = op_id.puid
        if other_puid not in self.clocks:
            self.clocks[other_puid] = CRDTClock(other_puid)
        self.clocks[other_puid].update(op.op_id)

    @synchronized
    def merge(self, vc):
        """
        Merge incoming vector clock with this one
        """
        for puid, clock in vc.iteritems():
            if puid in self.clocks:
                self.clocks[puid].update(clock)
            else:
                # we aren't aware of this peer
                logging.warn('wasn\'t aware of peer {}'.format(puid))
                pass

    @synchronized
    def add_peer(self, puid):
        """
        Add a clock entry for the peer
        """
        if puid in self.clocks:
            logging.warn('already had peer {}'.format(puid))
        self.clocks[puid] = CRDTClock(puid)

    @synchronized
    def remove_peer(self, puid):
        """
        Remove the clock entry for the peer
        """
        if puid in self.clocks:
            del self.clocks[puid]
        else:
            # peer not found?
            logging.error('peer not found {}'.format(puid))

    @synchronized
    def iterate(self):
        return self.clocks.items()

    @synchronized
    def __cmp__(self, other):
        if isinstance(other, CRDTClock):
            other_puid = other.puid
            my_version = self.clocks[other_puid]
            return cmp(my_version, other)

    @synchronized
    def pickle(self):
        return pickle.dumps(self)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return '|'.join(str(cl) for cl in self.clocks.itervalues())
