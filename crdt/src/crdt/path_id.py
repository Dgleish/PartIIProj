import math

from crdt.identifier import Identifier


class PathId(Identifier):
    def __init__(self, puid, num, depth=1):
        super().__init__(puid)
        self.num = num
        self.basebase = 4
        self.num_list = []
        d = depth
        while d > 0:
            base = self.get_base_for_depth(d)
            mask = ((1 << base) - 1)
            self.append(mask & num)
            num >>= base
            d -= 1
        self.num_list.reverse()

    def get_num(self, maxdepth=math.inf):
        res = 0
        for i in range(min(len(self.num_list), maxdepth)):
            # no that base for depth is the wrong way round
            res <<= (self.get_base_for_depth(i + 1))
            res += (self.num_list[i])
        return res

    def append(self, x):
        self.num_list.append(x)

    def get_size(self) -> int:
        return len(self.num_list)

    def get_base_for_depth(self, depth) -> int:
        return self.basebase + depth

    def __lt__(self, other):
        if isinstance(other, PathId):
            if self.num == other.num:
                if self.puid is not None:
                    return self.puid < other.puid
                else:
                    return False
            else:
                other_len = len(other.num_list)
                for i in range(min(other_len, len(self.num_list))):
                    x = self.num_list[i]
                    if x > other.num_list[i]:
                        return False
                    if x < other.num_list[i]:
                        return True
                return len(self.num_list) < len(other.num_list)

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    def __str__(self):
        return '{}:{}'.format(self.num_list, self.puid)

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        if self.puid is None:
            return hash(self.get_num())
        else:
            return hash(self.puid + str(self.get_num()))

    def __eq__(self, other):
        if self.puid is not None:
            return ((self.puid == other.puid)
                    and self.num_list == other.num_list)
        else:
            return self.num_list == other.num_list

    def prefix(self, depth):
        if depth <= len(self.num_list):
            return self.get_num(depth)
        else:
            # need to pad
            short_num = self.get_num()
            k = len(self.num_list)
            while k < depth:
                short_num <<= (self.get_base_for_depth(k + 1))
                k += 1
            return short_num

    def trim(self, depth):
        return self.get_num(depth)

    def at(self, depth):
        return self.num_list[depth - 1]
