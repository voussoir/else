import time


class Ratelimiter:
    def __init__(self, allowance, period=1, operation_cost=1, mode='sleep'):
        '''
        allowance:
            Our spending balance per `period` seconds.

        period:
            The number of seconds over which we can perform `allowance` operations.

        operation_cost:
            The default amount to remove from our balance after each operation.
            Pass a `cost` parameter to `self.limit` to use a nondefault value.

        mode:
            'sleep':
                If we do not have the balance for an operation, sleep until we do.
                Return True every time.

            'reject':
                If we do not have the balance for an operation, return False.
                The cost is not subtracted, so hopefully we have enough next time.
        '''
        if mode not in ('sleep', 'reject'):
            raise ValueError('Invalid mode %s' % repr(mode))

        self.allowance = allowance
        self.period = period
        self.operation_cost = operation_cost
        self.mode = mode

        self.last_operation = time.time()
        self.balance = 0

    @property
    def gain_rate(self):
        return self.allowance / self.period

    def limit(self, cost=None):
        '''
        See the main class docstring for info about cost and mode behavior.
        '''
        if cost is None:
            cost = self.operation_cost

        time_diff = time.time() - self.last_operation
        self.balance += time_diff * self.gain_rate
        self.balance = min(self.balance, self.allowance)

        if self.balance >= cost:
            self.balance -= cost
            succesful = True
        else:
            if self.mode == 'reject':
                succesful = False
            else:
                deficit = cost - self.balance
                time_needed = deficit / self.gain_rate
                time.sleep(time_needed)
                self.balance = 0
                succesful = True

        self.last_operation = time.time()
        return succesful
