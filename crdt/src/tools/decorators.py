from threading import RLock

from wrapt import decorator


@decorator
def synchronized(wrapped, instance, args, kwargs):
    if instance is None:
        context = vars(wrapped)
    else:
        context = vars(instance)

    lock = context.get('_synchronized_lock', None)

    if lock is None:
        lock = context.setdefault('_synchronized_lock', RLock())
    with lock:
        return wrapped(*args, **kwargs)
