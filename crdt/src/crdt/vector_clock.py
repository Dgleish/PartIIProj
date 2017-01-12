import logging
from threading import Lock

from crdt.crdt_ops import RemoteCRDTOp
from crdt_clock import CRDTClock


class VectorClock(object):
    def __init__(self, owner_clock):
        assert isinstance(owner_clock, CRDTClock)
        self.owner_puid = owner_clock.puid
        self.clocks = {self.owner_puid: owner_clock}
        self.vc_lock = Lock()

    def __getstate__(self):
        return {
            'owner_puid': self.owner_puid,
            'clocks': self.clocks,
        }

    def __setstate__(self, state):
        self.owner_puid = state['owner_puid']
        self.clocks = state['clocks']
        # recreate lock, don't copy it from other place
        self.vc_lock = Lock()

    def get_clock(self, puid):
        val = None
        self.vc_lock.acquire()
        if puid in self.clocks:
            val = self.clocks[puid]
        self.vc_lock.release()
        return val

    def update(self, op):
        self.vc_lock.acquire()
        op_id = op.op_id
        other_puid = op_id.puid
        if not other_puid in self.clocks:
            self.clocks[other_puid] = CRDTClock(other_puid)
        self.clocks[other_puid].increment()
        self.vc_lock.release()

    def merge(self, vc):
        self.vc_lock.acquire()
        for puid, clock in vc.iteritems():
            if puid in self.clocks:
                self.clocks[puid].update(clock)
            else:
                # we aren't aware of this peer
                logging.warn('wasn\'t aware of peer {}'.format(puid))
                pass
        self.vc_lock.release()

    def add_peer(self, puid):
        self.vc_lock.acquire()
        if puid in self.clocks:
            logging.warn('already had peer {}'.format(puid))
        self.clocks[puid] = CRDTClock(puid)
        self.vc_lock.release()

    def remove_peer(self, puid):
        self.vc_lock.acquire()
        if puid in self.clocks:
            del self.clocks[puid]
        else:
            # peer not found?
            logging.error('peer not found {}'.format(puid))
        self.vc_lock.release()

    def iterate(self):
        self.vc_lock.acquire()
        for puid, timestamp in self.clocks.iteritems():
            yield (puid, timestamp)
        self.vc_lock.release()

    def is_next_op(self, op):
        self.vc_lock.acquire()
        result = False
        """

        :type op: RemoteCRDTOp
        """
        # op id is a CRDTClock
        assert isinstance(op, RemoteCRDTOp)
        try:
            op_id = op.op_id
            other_puid = op_id.puid
            if other_puid in self.clocks:
                result = op_id.timestamp == self.clocks[other_puid].timestamp + 1
            else:
                result = op_id.timestamp == 1
        except AttributeError as e:
            logging.error('AE: {} {}'.format(dir(op), e))
        self.vc_lock.release()
        return result

    def __cmp__(self, other):
        if isinstance(other, CRDTClock):
            other_puid = other.puid
            my_version = self.clocks[other_puid]
            return cmp(my_version, other)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return '|'.join(str(cl) for cl in self.clocks.itervalues())
