import logging
import socket
import threading
from Queue import Queue
from logging.config import fileConfig
from random import randint
from time import sleep

from crdt.crdt_ops import CRDTOpAddRightLocal, CRDTOpDeleteLocal
from crdt.list_crdt import ListCRDT
from crdt.ll_ordered_list import LLOrderedList
from crdt_network_client import CRDTNetworkClient

fileConfig('../logging_config.ini')
logger = logging.getLogger('app')


class CRDTApp(object):
    def __init__(self, client_uid):
        # create the ListCRDT structure
        self.uid = client_uid
        self.crdt = ListCRDT(client_uid, LLOrderedList())

        # queue of operations consumed continuously in another thread
        self.op_queue = Queue()
        self.op_queue_sem = threading.Semaphore(0)
        op_queue_consumer = threading.Thread(
            target=self.consume_op_queue
        )
        # op_queue_consumer.daemon = True

        # be nice to pass this in as argument then have CRDTNetwork as an interface to
        # either cl-sv or P2P
        self.network_client = CRDTNetworkClient(
            socket.gethostname(), 12346, self.op_queue, self.op_queue_sem, self.uid
        )
        self.network_client.connect()

        ops_to_do = [CRDTOpDeleteLocal(), CRDTOpAddRightLocal(self.uid)]

        op_queue_consumer.start()
        self.simulate_user_input(ops_to_do)

    def simulate_user_input(self, ops_to_do):
        while len(ops_to_do) > 0:
            sleep(randint(0, 4))
            self.op_queue.put(ops_to_do.pop())
            self.op_queue_sem.release()

    def consume_op_queue(self):
        # logger.info('{} started op queue consumer'.format(self.uid))
        while True:
            self.op_queue_sem.acquire()
            op = self.op_queue.get()
            # logger.info('{} got operation {}'.format(self.uid, op))
            # TODO: handle exceptions better here
            op_to_send = self.crdt.perform_op(op)
            logger.debug('{}\'s state is now {}'.format(self.uid, self.crdt.pretty_print()))
            if op_to_send is not None:
                self.network_client.send_op(op_to_send)


if __name__ == '__main__':
    for i in xrange(2):
        CRDTApp(chr(ord('A') + i))
