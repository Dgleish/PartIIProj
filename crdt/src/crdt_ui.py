import threading

from crdt.crdt_ops import CRDTOpAddRightLocal, CRDTOpDeleteLocal


class CRDTLocalClient(object):
    def __init__(self, op_queue):
        self.op_q = op_queue
        key_listener = threading.Thread(target=self.listen_for_input)
        key_listener.daemon = True
        key_listener.start()

    def listen_for_input(self):
        while True:
            char = raw_input()
            if char == '\x08':
                self.op_q.appendleft(CRDTOpDeleteLocal())
            else:
                self.op_q.appendleft(CRDTOpAddRightLocal(char))
