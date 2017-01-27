import threading
from collections import deque


# noinspection PyArgumentList
class OperationQueue(object):
    # wrapper around a deque with signalling semaphore

    def __init__(self):
        self.queue = deque()
        self.q_sem = threading.Semaphore(0)

    def append(self, op):
        self.queue.append(op)
        self.q_sem.release()

    def appendleft(self, op):
        self.queue.appendleft(op)
        self.q_sem.release()

    def pop(self):
        self.q_sem.acquire()
        return self.queue.pop()

    def popleft(self):
        self.q_sem.acquire()
        return self.queue.popleft()
