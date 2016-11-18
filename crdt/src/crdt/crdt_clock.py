class CRDTClock(object):
    def __init__(self, uid, initial_timestamp=1):
        self.timestamp = initial_timestamp
        self.uid = uid
        self.value = '{}:{}'.format(initial_timestamp, uid)

    def update(self, other_clock):
        if other_clock is not None:
            old_timestamp = self.timestamp
            new_timestamp = max(old_timestamp, other_clock.timestamp + 1)
            self.value = '{}:{}'.format(new_timestamp, self.uid)

    def increment(self):
        self.timestamp += 1
        self.value = '{}:{}'.format(self.timestamp, self.uid)

    def can_do(self, other_clock):
        if other_clock is None:
            return True
        else:
            return other_clock.timestamp <= self.timestamp + 1

    def __cmp__(self, other_clock):
        if other_clock is None:
            return False
        assert isinstance(other_clock, CRDTClock)
        return cmp(self.value, other_clock.value)

    def __hash__(self):
        return hash(self.value)
