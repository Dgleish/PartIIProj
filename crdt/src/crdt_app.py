import socket
import threading
from Queue import Queue
from logging.config import fileConfig
from random import randint
from time import sleep

from crdt.crdt_ops import CRDTOpAddRightLocal
from crdt.list_crdt import ListCRDT
from crdt.ll_ordered_list import LLOrderedList
from crdt_network_client import CRDTNetworkClient

fileConfig('../logging_config.ini')


class CRDTApp(object):
    def __init__(self, client_uid, host, port, ops_to_do, num_apps):
        self.num_apps = num_apps
        self.num_ops_to_do = len(ops_to_do)

        # create the ListCRDT structure
        self.uid = client_uid
        self.crdt = ListCRDT(client_uid, LLOrderedList())

        # queue of operations consumed continuously in another thread
        self.op_queue = Queue()
        self.op_queue_sem = threading.Semaphore(0)
        op_queue_consumer = threading.Thread(
            target=self.consume_op_queue
        )
        op_queue_consumer.daemon = True

        # be nice to pass this in as argument then have CRDTNetwork as an interface to
        # either cl-sv or P2P
        self.network_client = CRDTNetworkClient(
            host, port, self.op_queue, self.op_queue_sem, self.uid
        )
        self.network_client.connect()

        op_queue_consumer.start()

        # self.local_client = CRDTLocalClient(
        #     self.op_queue, self.op_queue_sem
        # )


        self.simulate_user_input(ops_to_do)

    def simulate_user_input(self, ops_to_do):
        while len(ops_to_do) > 0:
            sleep(randint(0, 1))
            self.op_queue.put(ops_to_do.pop())
            self.op_queue_sem.release()

    def consume_op_queue(self):
        # logging.info('{} started op queue consumer'.format(self.uid))
        while True:
            self.op_queue_sem.acquire()
            op = self.op_queue.get()
            # logging.info('{} got operation {}'.format(self.uid, op))
            # TODO: handle exceptions better here
            op_to_send = self.crdt.perform_op(op)
            # logging.debug('{}\'s state is now {}'.format(self.uid, self.crdt.detail_print()))
            if op_to_send is not None:
                # logging.info('sending {}'.format(op_to_send))
                self.network_client.send_op(op_to_send)
        self.network_client.close()
        return


if __name__ == '__main__':
    n = 20
    for i in xrange(n):
        CRDTApp(chr(ord('A') + i), socket.gethostname(), 12346, [CRDTOpAddRightLocal(chr(ord('a') + i))], n)
