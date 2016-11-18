import socket
import threading
from collections import deque, defaultdict
from logging.config import fileConfig
from random import randint
from time import sleep

from crdt.crdt_exceptions import VertexNotFound
from crdt.crdt_ops import CRDTOpAddRightLocal
from crdt.list_crdt import ListCRDT
from crdt.ll_ordered_list import LLOrderedList
from crdt_local_client import CRDTLocalClient
from crdt_network_client import CRDTNetworkClient

fileConfig('../logging_config.ini')


class CRDTApp(object):
    def __init__(self, client_uid, host, port, ops_to_do):

        # create the ListCRDT structure
        self.uid = client_uid
        self.crdt = ListCRDT(client_uid, LLOrderedList())

        # queue of operations consumed continuously in another thread
        self.op_queue = deque()
        self.op_queue_sem = threading.Semaphore(0)
        op_queue_consumer = threading.Thread(
            target=self.consume_op_queue
        )
        op_queue_consumer.daemon = True

        # dict of operations that have arrived out of order
        self.held_back_ops = defaultdict(list)

        # be nice to pass this in as argument then have CRDTNetwork as an interface to
        # either cl-sv or P2P
        self.network_client = CRDTNetworkClient(
            host, port, self.op_queue, self.op_queue_sem, self.uid
        )
        self.local_client = CRDTLocalClient(
            self.op_queue, self.op_queue_sem
        )

        # go go go
        self.network_client.connect()
        op_queue_consumer.start()

        self.simulate_user_input(ops_to_do)

    def simulate_user_input(self, ops_to_do):
        while len(ops_to_do) > 0:
            sleep(randint(0, 1))
            self.op_queue.appendleft(ops_to_do.pop())
            self.op_queue_sem.release()

    def consume_op_queue(self):
        while True:

            # get item from the queue
            self.op_queue_sem.acquire()
            op = self.op_queue.pop()

            # if too high in sequence need to wait for next message
            if not self.crdt.can_perform_op(op):
                self.held_back_ops[op.clock].append(op)
                continue

            # do the operation on the local CRDT
            try:
                op_to_send = self.crdt.perform_op(op)
            except VertexNotFound:
                continue
            # if we got something to send to others, send to others
            if op_to_send is not None:
                self.network_client.send_op(op_to_send)
                op = op_to_send

            # for all operations held back that reference nodes with
            # clocks one greater than the op just done,
            # add them to the front of the queue
            if op.clock is not None:
                op.clock.increment()
                if op.clock in self.held_back_ops.keys():
                    for new_op in self.held_back_ops[op.clock].itervalues():
                        self.op_queue.append(new_op)
                        self.op_queue_sem.release()
                    del self.held_back_ops[op.clock]
        self.network_client.close()
        return


if __name__ == '__main__':
    n = 5
    for i in xrange(n):
        CRDTApp(chr(ord('A') + i), socket.gethostname(), 12346, [CRDTOpAddRightLocal(chr(ord('a') + i))])
