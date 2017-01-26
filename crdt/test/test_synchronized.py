import pickle
import threading
from time import sleep

from wrapt import decorator


@decorator
def synchronized(wrapped, instance, args, kwargs):
    if instance is None:
        context = vars(wrapped)
    else:
        context = vars(instance)

    lock = context.get('_synchronized_lock', None)

    if lock is None:
        lock = context.setdefault('_synchronized_lock', threading.RLock())

    with lock:
        return wrapped(*args, **kwargs)


# noinspection PyArgumentList
class SyncClass(object):
    def __init__(self):
        self.a = 0
        self.d = {
            'a': 1,
            'b': 2,
            'c': 3,
            'd': 4,
            'e': 5
        }

    @synchronized
    def __getstate__(self):
        print('pickling')
        val = {
            'a': self.a
        }
        sleep(5)
        print('done pickling')
        return val

    @synchronized
    def sync_meth(self, arr):
        arr += ['sync_meth'] * 100

    @synchronized
    def sync_meth2(self, arr):
        arr.append('sync_meth2')

    @synchronized
    def pickle(self):
        return pickle.dumps(self)

    @synchronized
    def iter(self):
        return self.d

    def iterate(self):
        for k, v in self.iter().items():
            print(k, v)


def test_sync():
    s = SyncClass()
    arr = []
    t1 = threading.Thread(target=s.sync_meth, args=(arr,))
    t2 = threading.Thread(target=s.sync_meth2, args=(arr,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    assert arr[-1] == 'sync_meth2' and arr[-2] == 'sync_meth'
