import collections

class Cache:
    def __init__(self, maxlen):
        self.maxlen = maxlen
        self.cache = collections.OrderedDict()

    def __contains__(self, key):
        return key in self.cache

    def __getitem__(self, key):
        value = self.cache.pop(key)
        self.cache[key] = value
        return value

    def __len__(self):
        return len(self.cache)

    def __setitem__(self, key, value):
        try:
            self.cache.pop(key)
        except KeyError:
            if len(self.cache) >= self.maxlen:
                self.cache.popitem(last=False)
        self.cache[key] = value

    def clear(self):
        self.cache.clear()

    def get(self, key, fallback=None):
        try:
            return self[key]
        except KeyError:
            return fallback

    def pop(self, key):
        return self.cache.pop(key)

    def remove(self, key):
        try:
            self.pop(key)
        except KeyError:
            pass
