import copy
import logging
import os
import threading
from logging.config import fileConfig

from crdt.crdt_exceptions import VertexNotFound
from crdt.list_crdt import ListCRDT
from crdt.lseq_ordered_list import LSEQOrderedList
from crdt.vector_clock import VectorClock
from network.crdt_p2p_client import CRDTP2PClient
from network.crdt_server_client import CRDTServerClient
from tools.operation_queue import OperationQueue
from tools.operation_store import OperationStore
from tor.tor_controller import TorController
from ui.crdt_local_client import CRDTLocalClient

dir = os.path.dirname(__file__)
filename = os.path.join(dir, '../logging_config.ini')
fileConfig(filename)


class CRDTApp(object):
    def __init__(self, puid, port, my_addr, ops_to_do=None, server_address=None, known_peers=None,
                 encrypt=False, priv_key=None, auth_cookies=None, my_cookie=None):

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
        self.crdt = ListCRDT(puid, LSEQOrderedList(puid))

        crdt_clock = self.crdt.get_clock()

        # Keep track of the operations we've received
        self.seen_ops_vc = VectorClock(crdt_clock)

        # Keep track of the operations we've performed
        self.done_ops_vc = VectorClock(crdt_clock)

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
        self.local_client = CRDTLocalClient(my_addr, self.op_queue, self.crdt.move_cursor, self.toggle_connect)

        self.simulate_user_input(ops_to_do)

        # Start performing operations
        op_queue_consumer = threading.Thread(
            target=self.consume_op_queue,
        )
        op_queue_consumer.daemon = True
        op_queue_consumer.start()

        # self.connect()

        # Show GUI
        self.local_client.display()

    def connect(self):
        # go go go
        """
        Starts the peer discovery process and then starts listening for incoming connections
        """
        if self.use_tor:
            self.tor.connect()
        network_thread = threading.Thread(target=self.network_client.connect)
        network_thread.daemon = True
        network_thread.start()
        self.is_connected = True

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

    def simulate_user_input(self, ops_to_do):
        """
        Apply operations to the CRDT automatically
        :param ops_to_do: the operations to apply
        """
        while len(ops_to_do) > 0:
            self.op_queue.appendleft(ops_to_do.pop())

    def consume_op_queue(self):
        """
        Continually take operations from the central queue and do them
        """
        while True:

            # get item from the queue
            op = self.op_queue.pop()
            self.can_consume_sem.acquire()
            try:
                # do the operation on the local CRDT
                op_to_store, should_send = copy.deepcopy(self.crdt.perform_op(op))
                if op_to_store is None:
                    self.can_consume_sem.release()
                    continue
            except VertexNotFound as e:
                logging.warning('{} Failed to do op {}, {}'.format(self.puid, op, e))
                # add op indexed by the (missing) operation it was referencing
                self.held_back_ops.add_op(op.vertex_id, op)
                # logging.debug('releasing sem')
                self.can_consume_sem.release()
                # logging.debug('released sem')
                continue

            # Store operation
            self.op_store.add_op(op_to_store.op_id.puid, op_to_store)

            logging.debug('{} did and stored op {}'.format(self.puid, op_to_store))
            logging.debug('state is now {}'.format(self.crdt.detail_print()))

            # Update UI
            self.local_client.update(self.crdt.pretty_print())

            # if we've got something to send to others, send to others
            if should_send:
                self.network_client.send_op(op_to_store)
            else:
                # increment corresponding component of vector clock
                self.seen_ops_vc.update(op_to_store)
                self.done_ops_vc.update(op_to_store)

            # for all operations held back that reference nodes with
            # clocks equal to the op just done,
            # add them to the front of the queue
            recovery_clock = op_to_store.op_id
            if recovery_clock in self.held_back_ops.ops:
                for new_op in self.held_back_ops.get_ops_for_key(recovery_clock):
                    self.op_queue.append(new_op)
                self.held_back_ops.remove_ops_for_key(recovery_clock)

            self.can_consume_sem.release()
