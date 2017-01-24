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
        print 'pickling'
        val = {
            'a': self.a
        }
        sleep(5)
        print 'done pickling'
        return val

    @synchronized
    def sync_meth(self):
        print 'entered function'
        self.d['e'] = 0
        self.d['d'] = 0
        self.d['c'] = 0
        self.d['b'] = 0
        sleep(5)
        print 'leaving function'

    @synchronized
    def sync_meth2(self):
        print 'entered func2'
        sleep(5)
        print 'leaving func2'

    @synchronized
    def pickle(self):
        return pickle.dumps(self)

    @synchronized
    def iter(self):
        return self.d

    def iterate(self):
        for k, v in self.iter().iteritems():
            print k, v


def test_sync():
    s = SyncClass()
    t1 = threading.Thread(target=s.iterate)
    t2 = threading.Thread(target=s.sync_meth)
    t3 = threading.Thread(target=s.sync_meth2)
    t2.start()
    t1.start()

    t3.start()
    sleep(10)
