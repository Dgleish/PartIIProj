class CRDTClock(object):
    def __init__(self, puid, initial_timestamp=0):
        self._timestamp = initial_timestamp
        self._puid = puid
        self.value = '{}:{}'.format(initial_timestamp, puid)

    @property
    def puid(self):
        return self._puid

    @property
    def timestamp(self):
        return self._timestamp

    def update(self, other_clock):
        if other_clock is not None:
            old_timestamp = self._timestamp
            new_timestamp = max(old_timestamp, other_clock.timestamp + 1)
            self._timestamp = new_timestamp
            self.value = '{}:{}'.format(new_timestamp, self._puid)

    def increment(self):
        self._timestamp += 1
        self.value = '{}:{}'.format(self._timestamp, self._puid)

    def __cmp__(self, other_clock):
        if other_clock is None:
            return -1
        if isinstance(other_clock, CRDTClock):
            if self.timestamp == other_clock.timestamp:
                return cmp(self.puid, other_clock.puid)
            else:
                return cmp(self.timestamp, other_clock.timestamp)

        else:
            return cmp(self.timestamp, other_clock)

    def __hash__(self):
        return hash(self.value)

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value
