import collections
import math
import time

class RateMeter:
    def __init__(self, span):
        '''
        This class is used to calculate a rolling average of
        units per second over `span` seconds.

        Minimum span is 1 second.

        Set `span` to None to calculate unit/s over the lifetime of the object
        after the first digest, rather than over a span.
        This saves the effort of tracking timestamps. Don't just use a large number!
        '''
        if span is not None and span < 1:
            raise ValueError('Span must be >= 1')
        self.sum = 0
        self.span = span

        self.tracking = collections.deque()
        self.first_digest = None

    def digest(self, value):
        now = math.ceil(time.time())
        self.sum += value


        if self.span is None:
            if self.first_digest is None:
                self.first_digest = now
            return

        earlier = now - self.span
        while len(self.tracking) > 0 and self.tracking[0][0] < earlier:
            (timestamp, pop_value) = self.tracking.popleft()
            self.sum -= pop_value

        if len(self.tracking) == 0 or self.tracking[-1] != now:
            self.tracking.append([now, value])
        else:
            self.tracking[-1][1] += value

    def report(self):
        '''
        Return a tuple containing the running sum, the time span
        over which the rate is being calculated, and the rate in
        units per second.

        (sum, time_interval, rate)
        '''
        # Flush the old values, ensure self.first_digest exists.
        self.digest(0)

        if self.span is None:
            now = math.ceil(time.time())
            time_interval = now - self.first_digest
        else:
            # No risk of IndexError because the digest(0) ensures we have
            # at least one entry.
            time_interval = self.tracking[-1][0] - self.tracking[0][0]

        if time_interval == 0:
            return (self.sum, 0, self.sum)
        rate = self.sum / time_interval
        time_interval = round(time_interval, 3)
        rate = round(rate, 3)
        return (self.sum, time_interval, rate)
