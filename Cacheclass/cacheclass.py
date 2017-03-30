import collections
import time
class Cache:
    def __init__(self, maxlen=None):
        self.maxlen = maxlen
        self._dict = {}
        #self._order = collections.deque()
        self._recency = {}

    def __getitem__(self, key):
        value = self._dict[key]
        self._maintain(key)
        return value

    def __setitem__(self, key, value):
        self._shrink()
        self._dict[key] = value
        self._maintain(key)
        #print(self._dict, self._recency)

    def _maintain(self, key):
        self._recency[key] = time.time()

    def _shrink(self):
        if self.maxlen is None:
            return

        pop_count = len(self._dict) - self.maxlen
        if pop_count < 1:
            return

        keys = sorted(self._recency.keys(), key=self._recency.get)
        for key in keys[:pop_count]:
            self._dict.pop(key)
            self._recency.pop(key)

    def get(self, key, fallback=None):
        try:
            return self[key]
        except KeyError:
            return fallback

    def remove(self, key):
        try:
            self._dict.pop(key)
            self._recency.pop(key)
        except KeyError:
            return
