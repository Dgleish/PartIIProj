import logging
import os
import threading
from logging.config import fileConfig
from time import process_time

from crdt.crdt_exceptions import VertexNotFound
from crdt.list_crdt import ListCRDT
from crdt.ops import RemoteOp, OpUndo, OpRedo
from crdt.ordered_list.lseq_ordered_list import LSEQOrderedList
from crdt.vector_clock import VectorClock
from network.clsv_client import CRDTServerClient
from network.p2p_client import CRDTP2PClient
from tools.operation_queue import OperationQueue
from tools.operation_store import OperationStore
from tor.tor_controller import TorController
from ui.crdt_local_client import CRDTLocalClient

curr_dir = os.path.dirname(__file__)
filename = os.path.join(curr_dir, '../logging_config.ini')
fileConfig(filename)


class CRDTApp(object):
    def __init__(self, puid, port, my_addr, ops_to_do=None, server_address=None, known_peers=None,
                 encrypt=False, priv_key=None, auth_cookies=None, my_cookie=None, list_repr=LSEQOrderedList):

        # logging.disable('DEBUG')

        if known_peers is None:
            known_peers = []

        if ops_to_do is None:
            ops_to_do = []

        # negotiate session key on connect and encrypt all operations sent
        self.encrypt = encrypt

        # connect through Tor
        if priv_key is not None:
            # Make Tor controller
            self.tor = TorController(port, priv_key, auth_cookies, my_cookie)
            self.use_tor = True
        else:
            self.use_tor = False

        # listening and/or connected to other peers?
        self.is_connected = False

        # ID to identify this instance of the application
        self.puid = puid

        # create the ListCRDT structure
        self.crdt = ListCRDT(puid, list_repr(puid))

        crdt_clock = self.crdt.get_clock()

        # Keep track of the operations we've received
        self.seen_ops_vc = VectorClock(crdt_clock)

        # queue of operations consumed continuously in another thread
        self.op_queue = OperationQueue()

        # store of operations by peer
        self.op_store = OperationStore(list)

        # dict of operations that have arrived out of order
        self.held_back_ops = OperationStore(set)

        # peers to connect to
        self.known_peers = known_peers

        # Semaphore to signal when allowed to perform operations
        # (Not when in the middle of connecting/disconnecting)
        self.can_consume_sem = threading.Semaphore(1)

        if server_address is None:
            # P2P
            self.network_client = CRDTP2PClient(
                port, self.op_queue, self.can_consume_sem, puid, self.seen_ops_vc,
                self.op_store, self.encrypt, self.known_peers, my_addr, priv_key is not None
            )
        else:
            self.network_client = CRDTServerClient(
                port, self.op_queue, self.can_consume_sem, puid, self.seen_ops_vc,
                self.op_store, self.encrypt, server_address)

        # local UI input
        self.local_client = CRDTLocalClient(
            my_addr, self.op_queue, self.crdt.move_cursor, self.toggle_connect, self.do_ops
        )

        self.simulate_user_input(ops_to_do)

        # Start performing operations
        # op_queue_consumer = threading.Thread(
        #     target=self.consume_op_queue
        # )
        # op_queue_consumer.daemon = True
        # op_queue_consumer.start()

        # # for timing stuff
        # timings = []
        # for _ in range(10000):
        #     self.crdt.perform_op(CRDTOpAddRightLocal('a'))
        # self.res = self.consume_op_queue_time(timings)

        # # TOR MEASUREMENT
        self.consume_op_queue()
        self.connect()

        # Show GUI
        # self.local_client.display()

    def time(self):
        self.local_client.destroy()
        return self.res

    def connect(self):
        # go go go
        """
        Starts the peer discovery process and then starts listening for incoming connections
        """
        if self.use_tor:
            self.tor.connect()

        # LENGTH_MEASUREMENT
        # network_thread = threading.Thread(target=self.network_client.connect)
        # network_thread.daemon = True
        # network_thread.start()
        self.network_client.connect()

        logging.debug('connecting over')
        self.is_connected = True
        if self.use_tor:
            self.tor.disconnect()

    def disconnect(self):
        """
        Drop all connections and stop listening for incoming connections
        """
        self.network_client.disconnect()
        if self.use_tor:
            self.tor.disconnect()
        self.is_connected = False

    def toggle_connect(self):
        """
        Toggle between a connected and disconnected state
        """
        if self.is_connected:
            self.disconnect()
        else:
            self.connect()

    def do_ops(self):
        op_queue_consumer = threading.Thread(
            target=self.consume_op_queue,
        )
        op_queue_consumer.daemon = True
        op_queue_consumer.start()

    def simulate_user_input(self, ops_to_do):
        """
        Apply operations to the CRDT automatically
        :param ops_to_do: the operations to apply
        """
        while len(ops_to_do) > 0:
            self.op_queue.appendleft(ops_to_do.pop())

    def recover(self, op_to_store):
        """
        For all operations held back that reference nodes with
        identifiers equal to the op just done, add them to the front of the queue
        """
        recovery_clock = op_to_store.op_id
        if recovery_clock in self.held_back_ops.ops:
            for new_op in self.held_back_ops.get_ops_for_key(recovery_clock):
                self.op_queue.append(new_op)
            self.held_back_ops.remove_ops_for_key(recovery_clock)

    def consume_op_queue(self):
        """
        Continually take operations from the central queue and do them
        """
        ops_done = 0
        while True:
            # get item from the queue
            op = self.op_queue.pop()
            self.can_consume_sem.acquire()

            if isinstance(op, OpUndo):
                op_to_undo = self.op_store.undo(self.puid)
                # if there was nothing to undo or redo, just ignore and move on
                if op_to_undo is None:
                    self.can_consume_sem.release()
                    continue
                op.set_op(op_to_undo)
                # logging.debug('got op {}'.format(op_to_undo))
            elif isinstance(op, OpRedo):
                op_to_undo = self.op_store.redo(self.puid)
                # if there was nothing to undo or redo, just ignore and move on
                if op_to_undo is None:
                    self.can_consume_sem.release()
                    continue
                op.set_op(op_to_undo)
                # logging.debug('got op {}'.format(op_to_undo))
            else:
                self.op_store.clear_undo()

            # logging.debug('about to do {}'.format(op))
            try:
                # do the operation on the local CRDT
                op_to_store, should_send = self.crdt.perform_op(op)
                assert isinstance(op_to_store, RemoteOp)
            except VertexNotFound as e:
                logging.warning('{} Failed to do op {}, {}'.format(self.puid, op, e))
                # add op indexed by the (missing) operation it was referencing
                self.held_back_ops.add_op(op.vertex_id, op)
                self.can_consume_sem.release()
                continue

            # Store operation and add to the undo stack if it was an undo
            self.op_store.add_op(op_to_store.op_id.puid, op_to_store, isinstance(op, OpUndo))
            # logging.debug('{} did and stored op {}'.format(self.puid, op_to_store))

            # Update UI
            # self.local_client.update(self.crdt.pretty_print())

            ops_done += 1
            if ops_done >= 100:
                self.can_consume_sem.release()
                return

            # if we've got something to send to others, send to others
            if should_send:
                self.network_client.send_op(op_to_store)
            else:
                # increment corresponding component of vector clock
                self.seen_ops_vc.update(op_to_store)

            self.recover(op_to_store)

            self.can_consume_sem.release()

    def consume_op_queue_time(self, timings):
        """
        Continually take operations from the central queue and do them
        """

        while True:
            curr_timing = []
            # get item from the queue
            op = self.op_queue.pop()
            # logging.debug('got op getting lock'.format())
            self.can_consume_sem.acquire()
            # logging.debug('got lock'.format())
            try:
                # do the operation on the local CRDT
                t = process_time()
                op_to_store, should_send = self.crdt.perform_op(op)
                curr_timing.append(process_time() - t)
                t1 = process_time()
                assert isinstance(op_to_store, RemoteOp)
            except VertexNotFound as e:
                logging.warning('{} Failed to do op {}, {}'.format(self.puid, op, e))
                # add op indexed by the (missing) operation it was referencing
                self.held_back_ops.add_op(op.clock, op)
                # logging.debug('releasing sem')
                self.can_consume_sem.release()
                # logging.debug('released sem')
                continue

            # Store operation
            self.op_store.add_op(op_to_store.op_id.puid, op_to_store)
            curr_timing.append(process_time() - t1)
            # t2 = process_time()
            # logging.debug('{} did and stored op {}'.format(self.puid, op_to_store))

            # Update UI
            # self.local_client.update(self.crdt.pretty_print())
            # curr_timing.append(process_time() - t2)
            t3 = process_time()
            # if we've got something to send to others, send to others
            if should_send:
                self.network_client.send_op(op_to_store)
            else:
                # increment corresponding component of vector clock
                self.seen_ops_vc.update(op_to_store)
            curr_timing.append(process_time() - t3)
            t4 = process_time()
            # for all operations held back that reference nodes with
            # clocks equal to the op just done,
            # add them to the front of the queue
            recovery_clock = op_to_store.op_id
            if recovery_clock in self.held_back_ops.ops:
                for new_op in self.held_back_ops.get_ops_for_key(recovery_clock):
                    self.op_queue.append(new_op)
                self.held_back_ops.remove_ops_for_key(recovery_clock)
            curr_timing.append(process_time() - t4)

            self.can_consume_sem.release()
            timings.append(curr_timing)
            if len(timings) == 50000:
                return timings
