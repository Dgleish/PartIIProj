from crdt.identifier import Identifier


class CRDTClock(Identifier):
    def __init__(self, puid, initial_timestamp=0):
        super().__init__(puid)
        self._timestamp = initial_timestamp
        self.value = '{}:{}'.format(initial_timestamp, puid)

    @property
    def timestamp(self):
        return self._timestamp

    def update(self, other_clock):
        if other_clock is not None:
            old_timestamp = self._timestamp
            new_timestamp = max(old_timestamp, other_clock.timestamp)
            self._timestamp = new_timestamp
            self.value = '{}:{}'.format(new_timestamp, self._puid)

    def increment(self):
        self._timestamp += 1
        self.value = '{}:{}'.format(self._timestamp, self._puid)

    def __eq__(self, other_clock):
        if other_clock is None:
            return False
        if isinstance(other_clock, CRDTClock):
            return (self.timestamp == other_clock.timestamp) and (self.puid == other_clock.puid)

    def __lt__(self, other_clock):
        if other_clock is None:
            return True
        if isinstance(other_clock, CRDTClock):
            if self.timestamp == other_clock.timestamp:
                return self.puid < other_clock.puid
            else:
                return self.timestamp < other_clock.timestamp

    def __hash__(self):
        return hash(self.value)

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value
