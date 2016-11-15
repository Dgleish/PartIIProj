import threading

from crdt.crdt_ops import CRDTOpAddRightLocal, CRDTOpDeleteLocal


class CRDTLocalClient(object):
    def __init__(self, op_queue, op_queue_sem):
        self.op_q = op_queue
        self.op_q_sem = op_queue_sem
        key_listener = threading.Thread(target=self.listen_for_input)
        key_listener.daemon = True
        key_listener.start()

    def listen_for_input(self):
        while True:
            char = raw_input()
            if char == '\x08':
                self.op_q.put(CRDTOpDeleteLocal())
            else:
                self.op_q.put(CRDTOpAddRightLocal(char))
            self.op_q_sem.release()
