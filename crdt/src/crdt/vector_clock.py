import logging
import pickle

from crdt.crdt_clock import CRDTClock
from tools.decorators import synchronized


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
                logging.warning('wasn\'t aware of peer {}'.format(puid))
                pass

    @synchronized
    def add_peer(self, puid):
        """
        Add a clock entry for the peer
        """
        if puid in self.clocks:
            logging.warning('already had peer {}'.format(puid))
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
    def __eq__(self, other):
        if isinstance(other, CRDTClock):
            # Essentially compares our corresponding clock component to
            # the given clock for equality
            other_puid = other.puid
            if other_puid in self.clocks:
                return other_puid in self.clocks and (self.clocks[other_puid] == other_puid)
            else:
                return False

    @synchronized
    def __lt__(self, other):
        if other is None:
            return False
        if isinstance(other, CRDTClock):
            # This is comparison is used to see if our vector clock
            # is behind a specific single clock
            # If we don't have an entry for it, it would default to 0
            # so we are definitely behind it
            other_puid = other.puid
            if other_puid in self.clocks:
                return self.clocks[other_puid] < other
            else:
                return True

    @synchronized
    def pickle(self):
        return pickle.dumps(self)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return '|'.join(str(cl) for cl in self.clocks.values())
