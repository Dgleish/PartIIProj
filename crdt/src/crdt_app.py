import copy
import logging
import threading
from collections import defaultdict
from random import randint
from time import sleep

from connected_peers import ConnectedPeers
from crdt.crdt_exceptions import VertexNotFound
from crdt.crdt_ops import RemoteCRDTOp
from crdt.list_crdt import ListCRDT
from crdt.ll_ordered_list import LLOrderedList
from crdt.vector_clock import VectorClock
from network.crdt_local_client import CRDTLocalClient
from network.crdt_p2p_client import CRDTP2PClient
from operation_queue import OperationQueue
from operation_store import OperationStore


class CRDTApp(object):
    def __init__(self, puid, host, port, ops_to_do, known_peers):

        # create the ListCRDT structure
        self.puid = puid
        self.crdt = ListCRDT(puid, LLOrderedList())

        crdt_clock = self.crdt.get_clock()
        self.seen_ops_vc = VectorClock(crdt_clock)

        self.done_ops_vc = VectorClock(crdt_clock)

        # queue of operations consumed continuously in another thread
        self.op_queue = OperationQueue()

        # store of operations by peer
        self.op_store = OperationStore()

        # store of connected peers
        self.connected_peers = ConnectedPeers()

        # dict of operations that have arrived out of order
        self.held_back_ops = defaultdict(list)

        # list of ops done when nobody else listening
        self.offline_ops = []

        # peers to connect to
        self.known_peers = known_peers

        self.local_client = CRDTLocalClient(self.op_queue, self.crdt.move_cursor)

        self.simulate_user_input(ops_to_do)

        op_queue_consumer = threading.Thread(
            target=self.consume_op_queue
        )
        op_queue_consumer.daemon = True
        op_queue_consumer.start()

        network_thread = threading.Thread(target=self.connect, args=(host, port))
        network_thread.daemon = True
        network_thread.start()

        self.local_client.display()

    def connect(self, host, port):
        # be nice to pass this in as argument then have CRDTNetwork as an interface to
        # either cl-sv or P2P
        self.network_client = CRDTP2PClient(
            host, port, self.op_queue, self.puid, self.seen_ops_vc,
            self.op_store, self.known_peers, self.connected_peers
        )
        # go go go
        self.network_client.connect(self.offline_ops)
        self.offline_ops = []

    def disconnect(self):
        pass

    def simulate_user_input(self, ops_to_do):
        while len(ops_to_do) > 0:
            sleep(randint(0, 1))
            self.op_queue.appendleft(ops_to_do.pop())

    def can_perform_op(self, op):
        # Check if the incoming operation's clock is no more than one ahead of ours
        # Otherwise its out of order and gets held back
        if isinstance(op, RemoteCRDTOp):
            # return self.clock.can_do(op.clock)
            return self.done_ops_vc.is_next_op(op)
        else:
            return True

    def consume_op_queue(self):
        while True:

            # get item from the queue
            op = self.op_queue.pop()

            # if too high in sequence need to wait for next message
            # if not self.can_perform_op(op):
            #     self.held_back_ops[op.op_id].append(op)
            #     logging.debug('{} holding back op {}'.format(self.puid, op))
            #     continue
            # else:
            #     logging.debug('{} about to do op {} in state {}'.format(self.puid, op, self.crdt.detail_print()))

            # do the operation on the local CRDT

            try:
                op_to_store, should_send = copy.deepcopy(self.crdt.perform_op(op))
            except VertexNotFound as e:
                logging.warn('{} Failed to do op {}, {}'.format(self.puid, op, e))
                continue

            self.op_store.add_op(op_to_store)
            logging.debug('{} stored op {} giving {}'.format(self.puid, op_to_store, self.crdt.detail_print()))
            self.local_client.update(self.crdt.pretty_print())
            # if we've got something to send to others, send to others
            if should_send:
                if self.connected_peers.is_empty():
                    self.offline_ops.append(op_to_store)
                else:
                    self.network_client.send_op(op_to_store)
            else:
                # increment corresponding component of vector clock
                # TODO: move this earlier so that we don't ask everyone for the same ops
                # TODO: but still need to be able to check if we are about to do the next operation in sequence
                logging.debug('about to update vector clock {}'.format(self.done_ops_vc))
                self.seen_ops_vc.update(op_to_store)
                self.done_ops_vc.update(op_to_store)

            logging.debug('vector clock is now {}'.format(self.done_ops_vc))

            # for all operations held back that reference nodes with
            # clocks one greater than the op just done,
            # add them to the front of the queue

            recovery_clock = copy.copy(op_to_store.op_id)
            recovery_clock.increment()
            if recovery_clock in self.held_back_ops:
                for new_op in self.held_back_ops[recovery_clock]:
                    self.op_queue.append(new_op)
                del self.held_back_ops[recovery_clock]
        self.network_client.close()
        return
